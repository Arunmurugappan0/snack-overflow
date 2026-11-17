import os
from pathlib import Path

from dotenv import load_dotenv
from flask_migrate import upgrade

from app import create_app, db
from app.models import Snack, User

ADMIN_EMAIL = "admin@snackoverflow.local"
MEMBER_EMAIL = "member@snackoverflow.local"
ADMIN_NAME = "Admin"
MEMBER_NAME = "Member"

STARTER_SNACKS = (
    ("Masala Peanuts", "savoury", 3),
    ("Chocolate Biscuits", "sweet", 18),
    ("Potato Chips", "savoury", 0),
    ("Orange Juice", "drink", 12),
    ("Trail Mix", "healthy-ish", 7),
)


def seed_demo_data(app, admin_password, member_password):
    with app.app_context():
        upgrade()

        created_users = 0
        for email, name, role, password in (
            (ADMIN_EMAIL, ADMIN_NAME, "admin", admin_password),
            (MEMBER_EMAIL, MEMBER_NAME, "member", member_password),
        ):
            if User.query.filter_by(email=email).first() is not None:
                continue
            if not password or not password.strip():
                variable = "SEED_ADMIN_PASSWORD" if role == "admin" else "SEED_MEMBER_PASSWORD"
                raise RuntimeError(
                    f"{variable} must be set before creating the demo {role}"
                )
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            created_users += 1

        added_snacks = 0
        for name, category, quantity in STARTER_SNACKS:
            if Snack.query.filter_by(name=name).first() is not None:
                continue
            db.session.add(Snack(name=name, category=category, quantity=quantity))
            added_snacks += 1

        db.session.commit()
        return {"users": created_users, "snacks": added_snacks}


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")
    app = create_app()
    result = seed_demo_data(
        app,
        os.getenv("SEED_ADMIN_PASSWORD"),
        os.getenv("SEED_MEMBER_PASSWORD"),
    )
    print(
        "Seed complete "
        f"(demo users created: {result['users']}; snacks added: {result['snacks']})."
    )


if __name__ == "__main__":
    main()
