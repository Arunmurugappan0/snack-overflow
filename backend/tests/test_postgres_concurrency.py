import concurrent.futures
import json
import os
import secrets
import threading
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from werkzeug.serving import make_server

from app import create_app, db
from app.models import Activity, Snack, User, Vote


def _consume(url, token, snack_id):
    request = Request(
        f"{url}/api/snacks/{snack_id}/consume",
        data=json.dumps({"amount": 1}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.status
    except HTTPError as error:
        error.read()
        return error.code


def test_postgres_concurrent_consumption_is_atomic():
    if os.getenv("RUN_POSTGRES_CONCURRENCY") != "1":
        pytest.skip("Set RUN_POSTGRES_CONCURRENCY=1 to run the PostgreSQL integration test")

    database_url = os.getenv("POSTGRES_TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        pytest.fail("POSTGRES_TEST_DATABASE_URL or DATABASE_URL must be configured")
    if make_url(database_url).get_backend_name() != "postgresql":
        pytest.fail("The concurrency test requires a PostgreSQL database URL")

    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": database_url,
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "pool_size": 10,
                "max_overflow": 0,
                "pool_timeout": 30,
            },
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "TESTING": False,
        }
    )

    user_id = None
    admin_id = None
    snack_id = None
    server = None
    server_thread = None
    try:
        with app.app_context():
            unique = uuid.uuid4().hex
            user = User(
                name="Concurrency test member",
                email=f"concurrency-{unique}@test.invalid",
                role="member",
            )
            user.set_password(uuid.uuid4().hex)
            admin = User(
                name="Concurrency test admin",
                email=f"concurrency-admin-{unique}@test.invalid",
                role="admin",
            )
            admin.set_password(uuid.uuid4().hex)
            snack = Snack(
                name=f"Concurrency test {unique}",
                category="savoury",
                quantity=3,
            )
            db.session.add_all([user, admin, snack])
            try:
                db.session.commit()
            except OperationalError:
                db.session.rollback()
                pytest.fail(
                    "PostgreSQL connection failed; verify the test database service and credentials.",
                    pytrace=False,
                )
            user_id = user.id
            admin_id = admin.id
            snack_id = snack.id
            token = create_access_token(identity=str(user_id))
            admin_token = create_access_token(identity=str(admin_id))
            db.session.add(Vote(user_id=user_id, snack_id=snack_id))
            db.session.commit()

            vote_constraints = inspect(db.engine).get_unique_constraints("vote")
            assert any(
                set(constraint["column_names"]) == {"user_id", "snack_id"}
                for constraint in vote_constraints
            ), "PostgreSQL vote table lacks UNIQUE(user_id, snack_id)"
            server_version, database_name = db.session.execute(
                text("SELECT current_setting('server_version'), current_database()")
            ).one()

        server = make_server("127.0.0.1", 0, app, threaded=True)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            statuses = list(
                executor.map(
                    lambda _: _consume(base_url, token, snack_id),
                    range(10),
                )
            )

        with app.app_context():
            final_quantity = db.session.get(Snack, snack_id).quantity
            activity_count = Activity.query.filter_by(
                snack_id=snack_id, action="consumed"
            ).count()

        assert statuses.count(200) == 3, statuses
        assert statuses.count(409) == 7, statuses
        assert final_quantity == 0
        assert activity_count == 3
        with app.test_client() as client:
            history = client.get(
                "/api/activity",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert history.status_code == 200
            assert history.json["total"] == 3
            assert all(item["user_id"] == user_id for item in history.json["items"])

            analytics = client.get(
                "/api/activity/summary",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert analytics.status_code == 200
            assert analytics.json["consumed_packets"] >= 3
            assert analytics.json["consume_events"] >= 3
            assert isinstance(analytics.json["top_consumed_snacks"], list)
            assert isinstance(analytics.json["top_favorite_snacks"], list)
            assert all(
                item["vote_count"] > 0
                for item in analytics.json["top_favorite_snacks"]
            )
        print(
            "PostgreSQL concurrency result: "
            f"server={server_version}, database={database_name}, "
            f"requests=10, successes={statuses.count(200)}, "
            f"conflicts={statuses.count(409)}, quantity={final_quantity}, "
            f"activities={activity_count}"
        )
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if server_thread is not None:
            server_thread.join(timeout=10)
        if snack_id is not None:
            with app.app_context():
                Activity.query.filter_by(snack_id=snack_id).delete(
                    synchronize_session=False
                )
                Vote.query.filter_by(snack_id=snack_id).delete(
                    synchronize_session=False
                )
                db.session.delete(db.session.get(Snack, snack_id))
                if user_id is not None:
                    db.session.delete(db.session.get(User, user_id))
                if admin_id is not None:
                    db.session.delete(db.session.get(User, admin_id))
                db.session.commit()
                db.engine.dispose()
