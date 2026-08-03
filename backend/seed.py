#!/usr/bin/env python3

from datetime import date
from app import create_app
from app.extensions import db
from app.models import User, Workout

app = create_app()

with app.app_context():
    print("Clearing database...")
    Workout.query.delete()
    User.query.delete()

    print("Creating users...")
    alice = User(username="alice", email="alice@example.com")
    alice.set_password("password123")

    bob = User(username="bob", email="bob@example.com")
    bob.set_password("password123")

    db.session.add_all([alice, bob])
    db.session.flush()

    print("Creating workouts...")
    db.session.add_all([
        Workout(title="Morning Run", duration=30, date=date(2026, 7, 1), notes="Easy pace", user_id=alice.id),
        Workout(title="Leg Day", duration=60, date=date(2026, 7, 3), notes="Squats and lunges", user_id=alice.id),
        Workout(title="Yoga", duration=45, date=date(2026, 7, 2), notes="Recovery session", user_id=bob.id),
    ])
    db.session.commit()
    print("Done!")