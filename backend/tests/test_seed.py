from sqlalchemy.engine import URL

from app import create_app, db
from app.models import Snack, User
from seed import seed_demo_data


def test_seed_is_idempotent_and_preserves_existing_records(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": URL.create(
                "sqlite",
                database=str(tmp_path / "seed-database.sqlite"),
            ),
            "JWT_SECRET_KEY": "seed-test-secret",
        }
    )

    first = seed_demo_data(app, "admin-seed-password", "member-seed-password")
    assert first == {"users": 2, "snacks": 5}

    with app.app_context():
        admin = User.query.filter_by(email="admin@snackoverflow.local").one()
        admin.set_password("existing-admin-password")
        Snack.query.filter_by(name="Masala Peanuts").one().quantity = 2
        db.session.commit()

    second = seed_demo_data(app, "new-admin-password", "new-member-password")
    assert second == {"users": 0, "snacks": 0}

    with app.app_context():
        assert User.query.count() == 2
        assert Snack.query.count() == 5
        assert User.query.filter_by(
            email="admin@snackoverflow.local"
        ).one().check_password("existing-admin-password")
        assert Snack.query.filter_by(name="Masala Peanuts").one().quantity == 2
