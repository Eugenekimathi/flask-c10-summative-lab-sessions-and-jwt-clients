from marshmallow import fields, validate, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from app.extensions import db
from app.models import User, Workout


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = False   # signup() builds the User by hand so it can hash the password
        sqla_session = db.session
        exclude = ("password_hash",)   # never serialize this out, ever

    # "password" isn't a real column — it's a write-only field the route
    # uses to call user.set_password(), then discards.
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6))


class WorkoutSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Workout
        load_instance = False
        sqla_session = db.session

    # id and user_id are server-assigned — the client should never set them,
    # so they're dump_only (serialize out, never accepted on load()).
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=150))
    duration = fields.Integer(required=True, validate=validate.Range(min=1))
    date = fields.Date(required=True)   # accepts "YYYY-MM-DD", returns a real date object
    notes = fields.String(required=False, allow_none=True)


user_schema = UserSchema()
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)