import secrets

from sqlalchemy import inspect, text

from app import create_app, db
from app.models import Activity, Snack, User, Vote

TEST_PASSWORD = secrets.token_urlsafe(32)


def setup_app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "JWT_SECRET_KEY": secrets.token_hex(32),
        }
    )
    with app.app_context():
        db.create_all()
        for name, email, role in [
            ("Admin", "a@test.local", "admin"),
            ("Member", "m@test.local", "member"),
        ]:
            user = User(name=name, email=email, role=role)
            user.set_password(TEST_PASSWORD)
            db.session.add(user)
        db.session.add(Snack(name="Test snack", category="savoury", quantity=3))
        db.session.commit()
    return app


def auth(client, email):
    response = client.post(
        "/api/auth/login", json={"email": email, "password": TEST_PASSWORD}
    )
    return {"Authorization": f"Bearer {response.json['access_token']}"}


def test_login_authentication_and_json_errors():
    app = setup_app()
    with app.test_client() as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/snacks").status_code == 401
        missing_token = client.get("/api/snacks")
        assert missing_token.json["error"]["code"] == "AUTHENTICATION_REQUIRED"

        login = client.post(
            "/api/auth/login",
            json={"email": "a@test.local", "password": TEST_PASSWORD},
        )
        assert login.status_code == 200
        assert login.json["user"]["name"] == "Admin"
        admin = {"Authorization": f"Bearer {login.json['access_token']}"}
        assert client.get("/api/auth/me", headers=admin).json["role"] == "admin"
        invalid_token = client.get(
            "/api/snacks", headers={"Authorization": "Bearer not-a-valid-token"}
        )
        assert invalid_token.status_code == 401
        assert invalid_token.json["error"]["code"] == "INVALID_TOKEN"
        invalid = client.post(
            "/api/auth/login",
            json={"email": "a@test.local", "password": TEST_PASSWORD + "-invalid"},
        )
        assert invalid.status_code == 401
        assert invalid.json["error"]["code"] == "INVALID_CREDENTIALS"
        malformed = client.post("/api/auth/login", json=[])
        assert malformed.status_code == 400
        assert malformed.json["error"]["code"] == "VALIDATION_ERROR"
        assert client.get("/api/unknown").json["error"]["code"] == "NOT_FOUND"
    with app.app_context():
        admin = User.query.filter_by(email="a@test.local").one()
        assert admin.password_hash != TEST_PASSWORD
        assert admin.check_password(TEST_PASSWORD)


def test_public_signup_creates_member_and_validates_fields():
    app = setup_app()
    with app.test_client() as client:
        signup = client.post(
            "/api/auth/register",
            json={
                "name": "  New Member  ",
                "email": " New.Member@Example.Test ",
                "password": "signup-password-123",
            },
        )
        assert signup.status_code == 201
        assert signup.json["user"] == {
            "id": 3,
            "name": "New Member",
            "email": "new.member@example.test",
            "role": "member",
        }
        assert signup.json["access_token"]
        headers = {"Authorization": f"Bearer {signup.json['access_token']}"}
        assert client.get("/api/auth/me", headers=headers).json["role"] == "member"

        duplicate = client.post(
            "/api/auth/register",
            json={
                "name": "Duplicate",
                "email": "NEW.MEMBER@example.test",
                "password": "signup-password-123",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

        invalid_requests = [
            {"name": "No email", "password": "signup-password-123"},
            {"name": "Bad email", "email": "not-an-email", "password": "signup-password-123"},
            {"name": "Short password", "email": "short@example.test", "password": "short"},
            {
                "name": "Privilege attempt",
                "email": "admin@example.test",
                "password": "signup-password-123",
                "role": "admin",
            },
        ]
        for request_data in invalid_requests:
            response = client.post("/api/auth/register", json=request_data)
            assert response.status_code == 400
            assert response.json["error"]["code"] == "VALIDATION_ERROR"

    with app.app_context():
        registered = User.query.filter_by(email="new.member@example.test").one()
        assert registered.role == "member"
        assert registered.password_hash != "signup-password-123"
        assert registered.check_password("signup-password-123")


def test_admin_crud_and_member_authorization():
    app = setup_app()
    with app.test_client() as client:
        member = auth(client, "m@test.local")
        admin = auth(client, "a@test.local")

        denied = client.post(
            "/api/snacks",
            headers=member,
            json={"name": "x", "category": "sweet", "quantity": 1},
        )
        assert denied.status_code == 403
        assert denied.json["error"]["code"] == "FORBIDDEN"
        assert client.patch(
            "/api/snacks/1", headers=member, json={"name": "Forbidden"}
        ).status_code == 403
        assert client.delete("/api/snacks/1", headers=member).status_code == 403
        assert client.post(
            "/api/snacks",
            headers=admin,
            json={"name": "New snack", "category": "sweet", "quantity": 8},
        ).status_code == 201
        assert client.post(
            "/api/snacks",
            headers=admin,
            json={"name": "New snack", "category": "sweet"},
        ).status_code == 409
        assert client.post(
            "/api/snacks",
            headers=admin,
            json={"name": "Bad snack", "category": ["sweet"]},
        ).status_code == 400

        updated = client.patch(
            "/api/snacks/1", headers=admin, json={"name": "Renamed snack"}
        )
        assert updated.status_code == 200
        assert updated.json["name"] == "Renamed snack"
        assert client.patch(
            "/api/snacks/1", headers=admin, json={"quantity": 99}
        ).status_code == 400
        assert client.get("/api/snacks/1", headers=member).status_code == 200
        assert client.get("/api/snacks/999", headers=member).status_code == 404
        assert client.delete("/api/snacks/999", headers=admin).status_code == 404
        assert client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": 1}
        ).status_code == 200
        assert client.delete("/api/snacks/1", headers=admin).status_code == 409
        assert client.delete("/api/snacks/2", headers=admin).status_code == 200


def test_stock_changes_are_atomic_and_role_protected():
    app = setup_app()
    with app.test_client() as client:
        member = auth(client, "m@test.local")
        admin = auth(client, "a@test.local")

        invalid = client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": True}
        )
        assert invalid.status_code == 400
        too_many = client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": 4}
        )
        assert too_many.status_code == 409
        assert too_many.json["error"]["code"] == "INSUFFICIENT_STOCK"
        assert client.post(
            "/api/snacks/1/restock", headers=member, json={"amount": 2}
        ).status_code == 403
        admin_consume = client.post(
            "/api/snacks/1/consume", headers=admin, json={"amount": 1}
        )
        assert admin_consume.status_code == 403
        assert admin_consume.json["error"]["code"] == "FORBIDDEN"

        consumed = client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": 2}
        )
        assert consumed.status_code == 200
        assert consumed.json["quantity"] == 1
        restocked = client.post(
            "/api/snacks/1/restock", headers=admin, json={"amount": 2}
        )
        assert restocked.status_code == 200
        assert restocked.json["quantity"] == 3

    with app.app_context():
        assert db.session.get(Snack, 1).quantity == 3
        activities = Activity.query.order_by(Activity.id).all()
        assert [(activity.action, activity.amount) for activity in activities] == [
            ("consumed", 2),
            ("restocked", 2),
        ]


def test_member_activity_history_is_private_and_admin_analytics_are_aggregated():
    app = setup_app()
    with app.test_client() as client:
        member = auth(client, "m@test.local")
        admin = auth(client, "a@test.local")

        empty_history = client.get("/api/activity", headers=member)
        assert empty_history.status_code == 200
        assert empty_history.json["total"] == 0
        assert empty_history.json["items"] == []
        assert client.get("/api/activity/summary", headers=admin).json == {
            "total_events": 0,
            "consumed_packets": 0,
            "restocked_packets": 0,
            "consume_events": 0,
            "restock_events": 0,
            "top_consumed_snacks": [],
            "top_favorite_snacks": [],
        }

        assert client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": 1}
        ).status_code == 200
        assert client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": 2}
        ).status_code == 200
        assert client.post(
            "/api/snacks/1/restock", headers=admin, json={"amount": 5}
        ).status_code == 200
        assert client.post(
            "/api/snacks/1/restock", headers=admin, json={"amount": 1}
        ).status_code == 200
        assert client.post(
            "/api/snacks",
            headers=admin,
            json={"name": "Another snack", "category": "sweet", "quantity": 2},
        ).status_code == 201
        assert client.post(
            "/api/snacks/2/consume", headers=member, json={"amount": 1}
        ).status_code == 200
        assert client.post("/api/snacks/1/vote", headers=member).status_code == 201
        assert client.post("/api/snacks/1/vote", headers=admin).status_code == 201
        assert client.post("/api/snacks/2/vote", headers=member).status_code == 201

        member_history = client.get(
            "/api/activity?page=1&per_page=2", headers=member
        )
        assert member_history.status_code == 200
        assert member_history.json["total"] == 3
        assert member_history.json["pages"] == 2
        assert len(member_history.json["items"]) == 2
        assert all(item["user_name"] == "Member" for item in member_history.json["items"])
        assert client.get("/api/activity?page=2&per_page=2", headers=member).json["items"][0][
            "snack_name"
        ] == "Test snack"

        admin_history = client.get("/api/activity", headers=admin)
        assert admin_history.status_code == 200
        assert admin_history.json["total"] == 5
        assert {item["user_name"] for item in admin_history.json["items"]} == {
            "Admin",
            "Member",
        }

        denied_summary = client.get("/api/activity/summary", headers=member)
        assert denied_summary.status_code == 403
        analytics = client.get("/api/activity/summary", headers=admin)
        assert analytics.status_code == 200
        assert analytics.json == {
            "total_events": 5,
            "consumed_packets": 4,
            "restocked_packets": 6,
            "consume_events": 3,
            "restock_events": 2,
            "top_consumed_snacks": [
                {
                    "snack_id": 1,
                    "snack_name": "Test snack",
                    "packets_consumed": 3,
                    "consume_events": 2,
                },
                {
                    "snack_id": 2,
                    "snack_name": "Another snack",
                    "packets_consumed": 1,
                    "consume_events": 1,
                },
            ],
            "top_favorite_snacks": [
                {
                    "snack_id": 1,
                    "snack_name": "Test snack",
                    "vote_count": 2,
                },
                {
                    "snack_id": 2,
                    "snack_name": "Another snack",
                    "vote_count": 1,
                },
            ],
        }

        invalid_page = client.get("/api/activity?page=0", headers=member)
        assert invalid_page.status_code == 400
        assert invalid_page.json["error"]["code"] == "VALIDATION_ERROR"


def test_stock_changes_roll_back_when_activity_insert_fails():
    app = setup_app()
    with app.app_context():
        db.session.execute(
            text(
                "CREATE TRIGGER fail_activity_insert BEFORE INSERT ON activity "
                "BEGIN SELECT RAISE(ABORT, 'forced activity insert failure'); END"
            )
        )
        db.session.commit()

    with app.test_client() as client:
        member = auth(client, "m@test.local")
        admin = auth(client, "a@test.local")

        failed_consume = client.post(
            "/api/snacks/1/consume", headers=member, json={"amount": 1}
        )
        assert failed_consume.status_code == 500
        assert failed_consume.json["error"]["code"] == "INTERNAL_SERVER_ERROR"

        failed_restock = client.post(
            "/api/snacks/1/restock", headers=admin, json={"amount": 1}
        )
        assert failed_restock.status_code == 500
        assert failed_restock.json["error"]["code"] == "INTERNAL_SERVER_ERROR"

    with app.app_context():
        assert db.session.get(Snack, 1).quantity == 3
        assert Activity.query.count() == 0


def test_votes_are_unique_user_scoped_and_removable():
    app = setup_app()
    with app.test_client() as client:
        member = auth(client, "m@test.local")
        admin = auth(client, "a@test.local")

        initial = client.get("/api/snacks/1/vote", headers=member)
        assert initial.status_code == 200
        assert initial.json == {"voted": False, "vote_count": 0, "created_at": None}
        assert client.post("/api/snacks/1/vote", headers=member).status_code == 201
        duplicate = client.post("/api/snacks/1/vote", headers=member)
        assert duplicate.status_code == 409
        assert duplicate.json["error"]["code"] == "ALREADY_VOTED"
        with app.app_context():
            constraints = inspect(db.engine).get_unique_constraints("vote")
            assert any(
                set(constraint["column_names"]) == {"user_id", "snack_id"}
                for constraint in constraints
            )

        voted = client.get("/api/snacks/1/vote", headers=member)
        assert voted.json["voted"] is True
        assert voted.json["vote_count"] == 1
        assert voted.json["created_at"]
        assert client.get("/api/snacks/1/vote", headers=admin).json["voted"] is False
        cannot_remove_other_users_vote = client.delete(
            "/api/snacks/1/vote", headers=admin
        )
        assert cannot_remove_other_users_vote.status_code == 404
        assert client.get("/api/snacks/1/vote", headers=member).json["voted"] is True
        assert client.delete("/api/snacks/1/vote", headers=member).status_code == 200
        assert client.get("/api/snacks/1/vote", headers=member).json["voted"] is False
        assert client.delete("/api/snacks/1/vote", headers=member).status_code == 404

    with app.app_context():
        assert Vote.query.count() == 0


def test_server_side_filters_search_pagination_and_summary():
    app = setup_app()
    with app.test_client() as client:
        admin = auth(client, "a@test.local")
        for snack in [
            {"name": "Apple juice", "category": "drink", "quantity": 0},
            {"name": "Brownie", "category": "sweet", "quantity": 10},
        ]:
            assert client.post("/api/snacks", headers=admin, json=snack).status_code == 201

        member = auth(client, "m@test.local")
        response = client.get(
            "/api/snacks?category=sweet&search=own&page=1&per_page=1",
            headers=member,
        )
        assert response.status_code == 200
        assert response.json["total"] == 1
        assert response.json["items"][0]["name"] == "Brownie"
        assert response.json["page"] == 1
        assert response.json["per_page"] == 1

        assert client.get(
            "/api/snacks?status=gone", headers=member
        ).json["items"][0]["name"] == "Apple juice"
        for query in ("?category=bad", "?status=bad", "?page=0", "?page=nope", "?per_page=101"):
            result = client.get(f"/api/snacks{query}", headers=member)
            assert result.status_code == 400
            assert result.json["error"]["code"] == "VALIDATION_ERROR"

        summary = client.get("/api/snacks/summary", headers=member)
        assert summary.status_code == 200
        assert summary.json["total"] == 3
        assert summary.json["stocked"] == 1
        assert summary.json["running_low"] == 1
        assert summary.json["gone"] == 1
        assert summary.json["snack_of_week"] is not None
