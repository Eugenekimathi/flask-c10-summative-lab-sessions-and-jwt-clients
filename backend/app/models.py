from datetime import datetime
from sqlalchemy.orm import validates
from app.extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workouts = db.relationship("Workout", backref="user", cascade="all, delete-orphan")

    @validates("username")
    def validate_username(self, key, value):
        if not value or len(value.strip()) < 3:
            raise ValueError("username must be at least 3 characters.")
        return value.strip()

    @validates("email")
    def validate_email(self, key, value):
        if not value or "@" not in value:
            raise ValueError("a valid email is required.")
        return value.strip().lower()

    def set_password(self, plain_password):
        self.password_hash = bcrypt.generate_password_hash(plain_password).decode("utf-8")

    def check_password(self, plain_password):
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        db.CheckConstraint("duration > 0", name="check_duration_positive"),
    )

    @validates("title")
    def validate_title(self, key, value):
        if not value or not value.strip():
            raise ValueError("title cannot be empty.")
        return value.strip()

    @validates("duration")
    def validate_duration(self, key, value):
        if value is None or value <= 0:
            raise ValueError("duration must be a positive integer.")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "duration": self.duration,
            "date": self.date.isoformat() if self.date else None,
            "notes": self.notes,
            "user_id": self.user_id,
        }

    def __repr__(self):
        return f"<Workout {self.title}>"