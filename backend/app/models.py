from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'member')", name="ck_user_role"),
    )
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Snack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    category = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=5)
    __table_args__ = (
        db.CheckConstraint("quantity >= 0", name="ck_quantity_nonnegative"),
        db.CheckConstraint("low_stock_threshold >= 0", name="ck_threshold_nonnegative"),
        db.CheckConstraint("category IN ('sweet','savoury','drink','healthy-ish')", name="ck_category"),
    )
    @property
    def status(self):
        if self.quantity == 0: return "gone"
        if self.quantity <= self.low_stock_threshold: return "running_low"
        return "stocked"
    def to_dict(self, votes=0, voted=False):
        return dict(id=self.id, name=self.name, category=self.category, quantity=self.quantity,
                    low_stock_threshold=self.low_stock_threshold, status=self.status,
                    vote_count=votes, voted=voted)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    snack_id = db.Column(db.Integer, db.ForeignKey("snack.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    __table_args__ = (db.UniqueConstraint("user_id", "snack_id", name="uq_vote_user_snack"),)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    snack_id = db.Column(db.Integer, db.ForeignKey("snack.id"), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (
        db.CheckConstraint(
            "action IN ('consumed', 'restocked')", name="ck_activity_action"
        ),
        db.CheckConstraint("amount > 0", name="ck_activity_amount_positive"),
    )
