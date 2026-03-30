from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()


# -------------------------
# USER
# -------------------------
class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="user")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship(
        "Task",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    categories = db.relationship(
        "Category",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# -------------------------
# CATEGORY
# -------------------------
class Category(db.Model):

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    tasks = db.relationship(
        "Task",
        backref="category",
        lazy=True
    )


# -------------------------
# TASK
# -------------------------
class Task(db.Model):

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)

    priority = db.Column(db.String(20), default="MEDIUM")

    completed = db.Column(db.Boolean, default=False)

    due_date = db.Column(db.Date)

    is_deleted = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id")
    )

    def to_dict(self):

        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "completed": self.completed,
            "due_date": self.due_date,
            "created_at": self.created_at,
            "category_id": self.category_id,
            "is_overdue": (
                not self.completed
                and self.due_date is not None
                and self.due_date < date.today()
            )
        }


# -------------------------
# ACTIVITY LOG
# -------------------------
class ActivityLog(db.Model):

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    action = db.Column(db.String(255), nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )