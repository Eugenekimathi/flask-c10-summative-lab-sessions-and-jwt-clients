from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Workout

workouts_bp = Blueprint("workouts", __name__)


def parse_date(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format.")
    return value


@workouts_bp.route("/workouts", methods=["GET"])
@jwt_required()
def get_workouts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)

    pagination = Workout.query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "workouts": [w.to_dict() for w in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
    }), 200


@workouts_bp.route("/workouts/<int:workout_id>", methods=["GET"])
@jwt_required()
def get_workout(workout_id):
    workout = Workout.query.get(workout_id)
    if not workout:
        return jsonify({"error": "Workout not found"}), 404
    return jsonify(workout.to_dict()), 200


@workouts_bp.route("/workouts", methods=["POST"])
@jwt_required()
def create_workout():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    try:
        workout = Workout(
            title=data.get("title"),
            duration=data.get("duration"),
            date=parse_date(data.get("date")),
            notes=data.get("notes"),
            user_id=user_id,
        )
        db.session.add(workout)
        db.session.commit()
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify(workout.to_dict()), 201


@workouts_bp.route("/workouts/<int:workout_id>", methods=["PATCH"])
@jwt_required()
def update_workout(workout_id):
    workout = Workout.query.get(workout_id)
    if not workout:
        return jsonify({"error": "Workout not found"}), 404

    data = request.get_json() or {}
    try:
        for field in ("title", "duration", "notes"):
            if field in data:
                setattr(workout, field, data[field])
        if "date" in data:
            workout.date = parse_date(data["date"])
        db.session.commit()
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify(workout.to_dict()), 200


@workouts_bp.route("/workouts/<int:workout_id>", methods=["DELETE"])
@jwt_required()
def delete_workout(workout_id):
    workout = Workout.query.get(workout_id)
    if not workout:
        return jsonify({"error": "Workout not found"}), 404

    db.session.delete(workout)
    db.session.commit()
    return jsonify({"message": "Workout deleted"}), 200