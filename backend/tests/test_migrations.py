from sqlalchemy import inspect
from sqlalchemy.engine import URL

from app import create_app, db
from app.models import User


def test_fresh_database_migrates_once_without_removing_data(tmp_path):
    database_url = URL.create(
        "sqlite",
        database=str(tmp_path / "fresh-database.sqlite"),
    )
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": database_url,
            "JWT_SECRET_KEY": "migration-test-secret",
        }
    )
    runner = app.test_cli_runner()

    first_upgrade = runner.invoke(args=["db", "upgrade"])
    assert first_upgrade.exit_code == 0, first_upgrade.output

    with app.app_context():
        assert {
            "user",
            "snack",
            "vote",
            "activity",
            "alembic_version",
        }.issubset(inspect(db.engine).get_table_names())
        db.session.add(
            User(
                name="Persisted user",
                email="persisted@example.test",
                password_hash="already-hashed",
                role="member",
            )
        )
        db.session.commit()

    second_upgrade = runner.invoke(args=["db", "upgrade"])
    assert second_upgrade.exit_code == 0, second_upgrade.output

    with app.app_context():
        assert User.query.filter_by(email="persisted@example.test").count() == 1
