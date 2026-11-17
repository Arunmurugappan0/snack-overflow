import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import case, func, text
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Activity, Snack, User, Vote

api = Blueprint("api", __name__)
CATEGORIES = {"sweet", "savoury", "drink", "healthy-ish"}
STATUSES = {"stocked", "running_low", "gone"}
MAX_INTEGER = 2_147_483_647


def err(code, message, status):
    return jsonify(error={"code": code, "message": message}), status


def request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def current_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def authenticated_user():
    user = current_user()
    if user is None:
        return None, err("AUTHENTICATION_REQUIRED", "A valid user account is required", 401)
    return user, None


def admin_user():
    user, error = authenticated_user()
    if error:
        return None, error
    if user.role != "admin":
        return None, err("FORBIDDEN", "Admin access required", 403)
    return user, None


def parse_integer_param(name, default, minimum, maximum):
    values = request.args.getlist(name)
    if not values:
        return default, None
    if len(values) != 1:
        return None, err("VALIDATION_ERROR", f"{name} must be provided once", 400)
    try:
        value = int(values[0])
    except ValueError:
        return None, err("VALIDATION_ERROR", f"{name} must be an integer", 400)
    if value < minimum or value > maximum:
        return None, err(
            "VALIDATION_ERROR",
            f"{name} must be between {minimum} and {maximum}",
            400,
        )
    return value, None


@api.get("/health")
def health():
    return jsonify(status="ok")


@api.post("/auth/login")
def login():
    data = request_data()
    if data is None:
        return err("VALIDATION_ERROR", "A JSON object is required", 400)
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password:
        return err("VALIDATION_ERROR", "Email and password are required", 400)

    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user or not user.check_password(password):
        return err("INVALID_CREDENTIALS", "Email or password is incorrect", 401)
    return jsonify(
        access_token=create_access_token(identity=str(user.id)),
        user={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    )


@api.post("/auth/register")
def register():
    data = request_data()
    if data is None:
        return err("VALIDATION_ERROR", "A JSON object is required", 400)
    if set(data) - {"name", "email", "password"}:
        return err("VALIDATION_ERROR", "Only name, email, and password are accepted", 400)

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name.strip()) > 120
        or not isinstance(email, str)
        or len(email.strip()) > 255
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip())
        or not isinstance(password, str)
        or len(password) < 8
        or len(password) > 128
    ):
        return err(
            "VALIDATION_ERROR",
            "Provide a name, valid email, and password between 8 and 128 characters",
            400,
        )

    user = User(name=name.strip(), email=email.strip().lower(), role="member")
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return err("EMAIL_ALREADY_REGISTERED", "An account with this email already exists", 409)

    return jsonify(
        access_token=create_access_token(identity=str(user.id)),
        user={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    ), 201


@api.get("/auth/me")
@jwt_required()
def whoami():
    user, error = authenticated_user()
    if error:
        return error
    return jsonify(id=user.id, name=user.name, email=user.email, role=user.role)


@api.get("/snacks")
@jwt_required()
def snacks():
    user, error = authenticated_user()
    if error:
        return error

    category = request.args.get("category")
    status = request.args.get("status")
    search = request.args.get("search", "")
    if category and category not in CATEGORIES:
        return err("VALIDATION_ERROR", "Invalid category", 400)
    if status and status not in STATUSES:
        return err("VALIDATION_ERROR", "Invalid status", 400)
    if len(search) > 120:
        return err("VALIDATION_ERROR", "Search must be 120 characters or fewer", 400)

    page, error = parse_integer_param("page", 1, 1, MAX_INTEGER)
    if error:
        return error
    per_page, error = parse_integer_param("per_page", 12, 1, 100)
    if error:
        return error

    query = Snack.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Snack.name.ilike(f"%{search}%", escape="\\"))
    if status == "gone":
        query = query.filter(Snack.quantity == 0)
    elif status == "running_low":
        query = query.filter(Snack.quantity > 0, Snack.quantity <= Snack.low_stock_threshold)
    elif status == "stocked":
        query = query.filter(Snack.quantity > Snack.low_stock_threshold)

    pagination = query.order_by(Snack.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    snack_ids = [snack.id for snack in pagination.items]
    if snack_ids:
        vote_counts = dict(
            db.session.query(Vote.snack_id, func.count(Vote.id))
            .filter(Vote.snack_id.in_(snack_ids))
            .group_by(Vote.snack_id)
            .all()
        )
        voted_ids = {
            vote.snack_id
            for vote in Vote.query.filter_by(user_id=user.id)
            .filter(Vote.snack_id.in_(snack_ids))
            .all()
        }
    else:
        vote_counts = {}
        voted_ids = set()

    return jsonify(
        items=[
            snack.to_dict(vote_counts.get(snack.id, 0), snack.id in voted_ids)
            for snack in pagination.items
        ],
        page=page,
        per_page=per_page,
        total=pagination.total,
        pages=pagination.pages,
    )


@api.get("/snacks/summary")
@jwt_required()
def summary():
    _, error = authenticated_user()
    if error:
        return error

    all_snacks = Snack.query.all()
    winner = (
        db.session.query(Snack, func.count(Vote.id))
        .outerjoin(Vote)
        .group_by(Snack.id)
        .order_by(func.count(Vote.id).desc(), Snack.name)
        .first()
    )
    return jsonify(
        total=len(all_snacks),
        stocked=sum(snack.status == "stocked" for snack in all_snacks),
        running_low=sum(snack.status == "running_low" for snack in all_snacks),
        gone=sum(snack.status == "gone" for snack in all_snacks),
        snack_of_week=winner[0].to_dict(winner[1]) if winner else None,
    )


@api.get("/activity")
@jwt_required()
def activity_history():
    user, error = authenticated_user()
    if error:
        return error

    page, error = parse_integer_param("page", 1, 1, MAX_INTEGER)
    if error:
        return error
    per_page, error = parse_integer_param("per_page", 10, 1, 100)
    if error:
        return error

    query = (
        db.session.query(Activity, Snack.name, User.name)
        .join(Snack, Activity.snack_id == Snack.id)
        .join(User, Activity.user_id == User.id)
    )
    if user.role != "admin":
        query = query.filter(Activity.user_id == user.id)

    pagination = query.order_by(
        Activity.created_at.desc(), Activity.id.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        items=[
            {
                "id": activity.id,
                "action": activity.action,
                "amount": activity.amount,
                "created_at": activity.created_at.isoformat(),
                "snack_id": activity.snack_id,
                "snack_name": snack_name,
                "user_id": activity.user_id,
                "user_name": user_name,
            }
            for activity, snack_name, user_name in pagination.items
        ],
        page=page,
        per_page=per_page,
        total=pagination.total,
        pages=pagination.pages,
    )


@api.get("/activity/summary")
@jwt_required()
def activity_summary():
    _, error = admin_user()
    if error:
        return error

    totals = db.session.query(
        func.count(Activity.id),
        func.coalesce(
            func.sum(
                case(
                    (Activity.action == "consumed", Activity.amount),
                    else_=0,
                )
            ),
            0,
        ),
        func.coalesce(
            func.sum(
                case(
                    (Activity.action == "restocked", Activity.amount),
                    else_=0,
                )
            ),
            0,
        ),
        func.sum(case((Activity.action == "consumed", 1), else_=0)),
        func.sum(case((Activity.action == "restocked", 1), else_=0)),
    ).one()

    top_consumed = (
        db.session.query(
            Snack.id,
            Snack.name,
            func.sum(Activity.amount).label("packets_consumed"),
            func.count(Activity.id).label("consume_events"),
        )
        .join(Activity, Activity.snack_id == Snack.id)
        .filter(Activity.action == "consumed")
        .group_by(Snack.id, Snack.name)
        .order_by(func.sum(Activity.amount).desc(), Snack.name.asc())
        .limit(5)
        .all()
    )
    top_favorites = (
        db.session.query(
            Snack.id,
            Snack.name,
            func.count(Vote.id).label("vote_count"),
        )
        .join(Vote, Vote.snack_id == Snack.id)
        .group_by(Snack.id, Snack.name)
        .order_by(func.count(Vote.id).desc(), Snack.name.asc())
        .limit(5)
        .all()
    )

    return jsonify(
        total_events=totals[0],
        consumed_packets=int(totals[1]),
        restocked_packets=int(totals[2]),
        consume_events=int(totals[3] or 0),
        restock_events=int(totals[4] or 0),
        top_consumed_snacks=[
            {
                "snack_id": snack_id,
                "snack_name": snack_name,
                "packets_consumed": int(packets_consumed),
                "consume_events": consume_events,
            }
            for snack_id, snack_name, packets_consumed, consume_events in top_consumed
        ],
        top_favorite_snacks=[
            {
                "snack_id": snack_id,
                "snack_name": snack_name,
                "vote_count": vote_count,
            }
            for snack_id, snack_name, vote_count in top_favorites
        ],
    )


@api.get("/snacks/<int:sid>")
@jwt_required()
def get_snack(sid):
    user, error = authenticated_user()
    if error:
        return error
    snack = db.session.get(Snack, sid)
    if snack is None:
        return err("NOT_FOUND", "Snack not found", 404)
    vote_count = Vote.query.filter_by(snack_id=sid).count()
    voted = Vote.query.filter_by(snack_id=sid, user_id=user.id).first() is not None
    return jsonify(snack.to_dict(vote_count, voted))


@api.post("/snacks")
@jwt_required()
def create_snack():
    _, error = admin_user()
    if error:
        return error
    data = request_data()
    if data is None:
        return err("VALIDATION_ERROR", "A JSON object is required", 400)
    if set(data) - {"name", "category", "quantity", "low_stock_threshold"}:
        return err("VALIDATION_ERROR", "Unknown snack fields", 400)

    name = data.get("name")
    category = data.get("category")
    quantity = data.get("quantity", 0)
    threshold = data.get("low_stock_threshold", 5)
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name.strip()) > 120
        or not isinstance(category, str)
        or category not in CATEGORIES
        or type(quantity) is not int
        or quantity < 0
        or quantity > MAX_INTEGER
        or type(threshold) is not int
        or threshold < 0
        or threshold > MAX_INTEGER
    ):
        return err("VALIDATION_ERROR", "Invalid snack fields", 400)

    snack = Snack(
        name=name.strip(),
        category=category,
        quantity=quantity,
        low_stock_threshold=threshold,
    )
    db.session.add(snack)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return err("DUPLICATE_SNACK", "Snack name already exists", 409)
    return jsonify(snack.to_dict()), 201


@api.patch("/snacks/<int:sid>")
@jwt_required()
def update_snack(sid):
    _, error = admin_user()
    if error:
        return error
    snack = db.session.get(Snack, sid)
    if snack is None:
        return err("NOT_FOUND", "Snack not found", 404)
    data = request_data()
    if data is None or not data:
        return err("VALIDATION_ERROR", "A non-empty JSON object is required", 400)
    if set(data) - {"name", "category", "low_stock_threshold"}:
        return err("VALIDATION_ERROR", "Unknown or non-editable snack fields", 400)

    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            return err("VALIDATION_ERROR", "Name must be between 1 and 120 characters", 400)
        snack.name = name.strip()
    if "category" in data:
        if not isinstance(data["category"], str) or data["category"] not in CATEGORIES:
            return err("VALIDATION_ERROR", "Invalid category", 400)
        snack.category = data["category"]
    if "low_stock_threshold" in data:
        threshold = data["low_stock_threshold"]
        if type(threshold) is not int or threshold < 0 or threshold > MAX_INTEGER:
            return err("VALIDATION_ERROR", "Invalid threshold", 400)
        snack.low_stock_threshold = threshold

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return err("DUPLICATE_SNACK", "Snack name already exists", 409)
    return jsonify(snack.to_dict())


@api.delete("/snacks/<int:sid>")
@jwt_required()
def delete_snack(sid):
    _, error = admin_user()
    if error:
        return error
    snack = db.session.get(Snack, sid)
    if snack is None:
        return err("NOT_FOUND", "Snack not found", 404)
    if Activity.query.filter_by(snack_id=sid).first() is not None:
        return err("SNACK_HAS_HISTORY", "Snack with activity history cannot be deleted", 409)
    Vote.query.filter_by(snack_id=sid).delete(synchronize_session=False)
    db.session.delete(snack)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return err("SNACK_HAS_HISTORY", "Snack with activity history cannot be deleted", 409)
    return jsonify(message="Snack deleted")


def stock_change(sid, amount, action):
    if type(amount) is not int or amount <= 0 or amount > MAX_INTEGER:
        return err("VALIDATION_ERROR", "Amount must be a positive 32-bit integer", 400)

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return err("AUTHENTICATION_REQUIRED", "A valid user account is required", 401)

    with db.session.begin():
        user = db.session.get(User, user_id)
        if user is None:
            return err("AUTHENTICATION_REQUIRED", "A valid user account is required", 401)
        if action == "consumed" and user.role != "member":
            return err("FORBIDDEN", "Only pantry members can consume snacks", 403)
        if action == "restocked" and user.role != "admin":
            return err("FORBIDDEN", "Admin access required", 403)

        if action == "consumed":
            update = text(
                "UPDATE snack SET quantity = quantity - :amount "
                "WHERE id = :sid AND quantity >= :amount "
                "RETURNING id, quantity"
            )
            parameters = {"amount": amount, "sid": sid}
        else:
            update = text(
                "UPDATE snack SET quantity = quantity + :amount "
                "WHERE id = :sid AND quantity <= :max_quantity - :amount "
                "RETURNING id, quantity"
            )
            parameters = {
                "amount": amount,
                "sid": sid,
                "max_quantity": MAX_INTEGER,
            }
        row = db.session.execute(update, parameters).fetchone()
        if row is None:
            exists = db.session.execute(
                text("SELECT 1 FROM snack WHERE id = :sid"), {"sid": sid}
            ).first()
            if not exists:
                return err("NOT_FOUND", "Snack not found", 404)
            if action == "restocked":
                return err("STOCK_LIMIT", "Snack quantity exceeds the supported limit", 409)
            return err(
                "INSUFFICIENT_STOCK",
                "Someone beat you to the last packet!",
                409,
            )

        db.session.add(
            Activity(user_id=user_id, snack_id=sid, action=action, amount=amount)
        )
        result = {"id": row.id, "quantity": row.quantity}

    return jsonify(**result, message="Stock updated")


@api.post("/snacks/<int:sid>/consume")
@jwt_required()
def consume(sid):
    data = request_data()
    if data is None:
        return err("VALIDATION_ERROR", "A JSON object is required", 400)
    if set(data) != {"amount"}:
        return err("VALIDATION_ERROR", "Only the amount field is accepted", 400)
    return stock_change(sid, data["amount"], "consumed")


@api.post("/snacks/<int:sid>/restock")
@jwt_required()
def restock(sid):
    data = request_data()
    if data is None:
        return err("VALIDATION_ERROR", "A JSON object is required", 400)
    if set(data) != {"amount"}:
        return err("VALIDATION_ERROR", "Only the amount field is accepted", 400)
    return stock_change(sid, data["amount"], "restocked")


@api.get("/snacks/<int:sid>/vote")
@jwt_required()
def get_vote(sid):
    user, error = authenticated_user()
    if error:
        return error
    if db.session.get(Snack, sid) is None:
        return err("NOT_FOUND", "Snack not found", 404)
    vote = Vote.query.filter_by(user_id=user.id, snack_id=sid).first()
    vote_count = Vote.query.filter_by(snack_id=sid).count()
    return jsonify(
        voted=vote is not None,
        vote_count=vote_count,
        created_at=vote.created_at.isoformat() if vote else None,
    )


@api.post("/snacks/<int:sid>/vote")
@jwt_required()
def vote(sid):
    user, error = authenticated_user()
    if error:
        return error
    if db.session.get(Snack, sid) is None:
        return err("NOT_FOUND", "Snack not found", 404)
    db.session.add(Vote(user_id=user.id, snack_id=sid))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return err("ALREADY_VOTED", "You have already voted for this snack", 409)
    return jsonify(message="Vote recorded"), 201


@api.delete("/snacks/<int:sid>/vote")
@jwt_required()
def unvote(sid):
    user, error = authenticated_user()
    if error:
        return error
    if db.session.get(Snack, sid) is None:
        return err("NOT_FOUND", "Snack not found", 404)
    vote = Vote.query.filter_by(user_id=user.id, snack_id=sid).first()
    if vote is None:
        return err("VOTE_NOT_FOUND", "Vote not found", 404)
    db.session.delete(vote)
    db.session.commit()
    return jsonify(message="Vote removed")
