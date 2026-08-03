# Workout Tracker API

A Flask + Flask-SQLAlchemy + Marshmallow REST API for tracking personal
workouts, secured with JWT authentication. Each user signs up, logs in, and
can only ever see, create, edit, or delete their **own** workouts — never
anyone else's. It shows the same two-layer defense pattern throughout:
**Marshmallow** validates incoming request data before a model is ever built,
and **SQLAlchemy constraints** (`unique`, `CheckConstraint`, `@validates`)
protect the database itself no matter what writes to it.

## Project layout

```
project/
├── Pipfile
├── Pipfile.lock
└── backend/
    ├── app/
    │   ├── __init__.py     # app factory, extensions, blueprint registration
    │   ├── config.py        # SQLALCHEMY_DATABASE_URI, JWT_SECRET_KEY
    │   ├── extensions.py     # db, migrate, bcrypt, jwt — created here, bound in __init__.py
    │   ├── models.py         # User, Workout — nullable, unique, CheckConstraint, @validates
    │   ├── schemas.py        # Marshmallow schemas — validate.Length/Range, load_only password
    │   ├── auth.py           # /signup, /login, /me
    │   └── routes.py         # /workouts CRUD, wired schema.load() -> model -> db.session.commit()
    ├── migrations/
    ├── seed.py
    └── run.py
```

## Setup

The `Pipfile` lives at the project root, one level above `backend/` — `pipenv install` runs from there, everything else runs from `backend/`, inside the same activated shell.

```bash
cd project/
pipenv install
pipenv shell

cd backend/
export FLASK_APP=run.py      # Windows: set FLASK_APP=run.py (cmd) or $env:FLASK_APP="run.py" (PowerShell)

flask db init                 # one-time only
flask db migrate -m "create users and workouts tables"
flask db upgrade

python seed.py                 # creates two sample users (alice, bob) with sample workouts
```

## Run it

```bash
python run.py
```

The API runs at `http://127.0.0.1:5555`.

## Endpoints

| Method | Route | Auth required | Description |
|---|---|---|---|
| `POST` | `/signup` | No | Create a new user account. Validates username/email/password via Marshmallow, then checks for duplicate username or email. Returns the new user and a JWT access token. |
| `POST` | `/login` | No | Authenticate with `username` + `password`. Returns the user and a JWT access token. |
| `GET` | `/me` | Yes | Return the currently authenticated user's own profile. |
| `GET` | `/workouts` | Yes | List the current user's workouts. Supports `?page=` and `?per_page=` (max 50) query parameters. |
| `GET` | `/workouts/<id>` | Yes | Get a single workout by ID — only if it belongs to the current user, otherwise `404`. |
| `POST` | `/workouts` | Yes | Create a new workout for the current user. Body: `title`, `duration` (minutes, > 0), `date` (`YYYY-MM-DD`), `notes` (optional). |
| `PATCH` | `/workouts/<id>` | Yes | Update one or more fields on a workout the current user owns. Any subset of `title`, `duration`, `date`, `notes`. |
| `DELETE` | `/workouts/<id>` | Yes | Delete a workout the current user owns. |

Every `/workouts*` route requires an `Authorization: Bearer <access_token>` header, obtained from `/signup` or `/login`.

## Try it — walking through every route

```bash
# 1. Sign up — Marshmallow rejects a bad payload before a model exists (400)
curl -X POST http://127.0.0.1:5555/signup -H "Content-Type: application/json" \
  -d '{"username":"al","email":"not-an-email","password":"123"}'

# Valid signup — succeeds (201), returns a token
curl -X POST http://127.0.0.1:5555/signup -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"password123"}'

# Duplicate username — passes Marshmallow, but the app-level uniqueness check catches it (409)
curl -X POST http://127.0.0.1:5555/signup -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"someone-else@example.com","password":"password123"}'

# 2. Log in — wrong password (401), missing fields (400), then correct credentials (200)
curl -X POST http://127.0.0.1:5555/login -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"wrongpass"}'

curl -X POST http://127.0.0.1:5555/login -H "Content-Type: application/json" -d '{}'

curl -X POST http://127.0.0.1:5555/login -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
# save the access_token from this response as $TOKEN below

# 3. /me — valid token (200), missing token (401), garbage token (401/422)
curl http://127.0.0.1:5555/me -H "Authorization: Bearer $TOKEN"
curl http://127.0.0.1:5555/me
curl http://127.0.0.1:5555/me -H "Authorization: Bearer garbage"

# 4. Create a workout — bad data rejected by the schema (400), then a valid one (201)
curl -X POST http://127.0.0.1:5555/workouts -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Bad","duration":-5,"date":"not-a-date"}'

curl -X POST http://127.0.0.1:5555/workouts -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Morning Run","duration":30,"date":"2026-07-01","notes":"Easy pace"}'

# 5. Read — list (200) and single workout (200), then a non-existent id (404)
curl "http://127.0.0.1:5555/workouts?page=1&per_page=10" -H "Authorization: Bearer $TOKEN"
curl http://127.0.0.1:5555/workouts/1 -H "Authorization: Bearer $TOKEN"
curl http://127.0.0.1:5555/workouts/9999 -H "Authorization: Bearer $TOKEN"

# 6. Update — partial patch (200)
curl -X PATCH http://127.0.0.1:5555/workouts/1 -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"duration": 40}'

# 7. Authorization — log in as a second user and confirm you can't touch the first user's data (404, not their data)
curl -X POST http://127.0.0.1:5555/login -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"password123"}'
# save this response's access_token as $TOKEN_BOB

curl http://127.0.0.1:5555/workouts/1 -H "Authorization: Bearer $TOKEN_BOB"
# expect 404 here, even though workout 1 genuinely exists — it just isn't Bob's

# 8. Delete — succeeds (200), then deleting the same id again fails (404)
curl -X DELETE http://127.0.0.1:5555/workouts/1 -H "Authorization: Bearer $TOKEN"
curl -X DELETE http://127.0.0.1:5555/workouts/1 -H "Authorization: Bearer $TOKEN"
```

## The core idea

| | Marshmallow validations | SQLAlchemy constraints |
|---|---|---|
| **Layer** | Application (schema) | Database |
| **When it runs** | On `schema.load()`, before a model exists | On `db.session.commit()` |
| **Good for** | Field format, ranges, friendly error messages | Data integrity no matter who or what writes |
| **Failure** | `ValidationError` → 400 with field messages | `IntegrityError` / `ValueError` → caught and returned as 400/409 |

Use both. Marshmallow gives the client a specific, friendly reason a request
failed before it ever touches the database. The constraint on the model is
what actually *guarantees* the rule can never be broken — even if a future
endpoint forgets to validate, or `seed.py` tries to insert something invalid
directly.

## Authorization

Every workout route scopes its query to `user_id` from the current JWT
identity — `Workout.query.filter_by(id=workout_id, user_id=current_user_id)`
rather than a plain `Workout.query.get(id)`. A user requesting someone else's
workout ID gets a `404`, identical to a genuinely non-existent ID —
deliberately not a `403`, since revealing "this ID exists but isn't yours"
would leak information about other users' data.