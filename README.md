# Robot Project Tracker

A personal workbench for robotics projects. Add a build, record parts and test notes, and move it through **Planned**, **Building**, **Testing**, and **Complete**. The browser board and REST API share the same SQLite records.

After starting Flask, open [the project board](http://127.0.0.1:5050/). Create an account or sign in, then select **Add project**. Select a project card to edit its notes or move it to another stage. Changes persist when you sign out.

## Ownership in SQLite

The initial migration creates `users` and `robot_builds`. The required `robot_builds.user_id` column references `users.id`. SQLite checks the foreign key on every application connection, so an insert with a missing or unknown owner fails. An index on `user_id` supports listing one developer's projects. The models use the foreign key directly, without an ORM relationship.

SQLite supplies UTC creation timestamps and the default account role, `user`. The email column has a unique constraint. Passwords are stored as Werkzeug hashes.

## Local setup

From the repository root, run the following in a macOS or Linux shell. The project has been tested with Python 3.13.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
flask --app robot_builds_api db upgrade
flask --app robot_builds_api run --port 5050
```

The development server listens at `http://127.0.0.1:5050`. Keep the same secret across restarts to keep issued tokens valid. To persist local configuration, copy `.env.example` to `.env`, set the generated key there, then run `set -a; source .env; set +a` before starting Flask. Git ignores that file.

| Variable | Purpose | Default |
| --- | --- | --- |
| `JWT_SECRET_KEY` | HS256 signing key. Use a randomly generated secret. | Required |
| `JWT_ACCESS_LIFETIME_MINUTES` | Positive integer access-token lifetime | `15` |
| `DATABASE_URL` | SQLAlchemy connection URI | `sqlite:///robot_builds.db` (under `instance/`) |

Use `flask --app robot_builds_api db current` to see the installed revision and `flask --app robot_builds_api db check` to check the models against the migrated database. For future schema changes, generate a revision with `db migrate -m "Describe the change"`, inspect it, and then run `db upgrade`. Revision `0001` initializes a fresh database. Revision `0002` adds the project stage and places existing builds in Planned. An existing unversioned database needs a migration tailored to its schema and verified owner IDs before adoption.

## Authentication and permissions

Login issues an HS256 access token. Protected routes verify the signature, expiration, and subject and load the current account from the database. Registration always creates a regular user. Administrators can manage all builds. Profile endpoints always refer to the signed-in account, including for administrators.

To grant admin access, register the account first and run this command from the configured application environment.

```sh
flask --app robot_builds_api promote-admin developer@example.com
```

## Endpoints

Send JSON request bodies with `Content-Type: application/json`. Protected routes require an `Authorization: Bearer <token>` header.

| Method | Path | Access | Result |
| --- | --- | --- | --- |
| POST | `/registration` | Public | Supply email and password. Returns the profile in `user` (201). |
| POST | `/login` | Public | Supply email and password. Returns `access_token` (200). |
| GET | `/me` | Signed in | Returns `user` with ID, email, and creation time. |
| PATCH, PUT | `/me` | Signed in | Supply only `email`. Returns the updated profile. |
| GET | `/admin/ping` | Admin | Returns `{"message":"pong"}`. |
| GET | `/robot-builds` | Signed in | Returns accessible builds in `robot_builds`, ordered by ID. |
| POST | `/robot-builds` | Signed in | Supply `name` and optional `description` and `stage`. Returns the new `robot_build` (201). |
| GET | `/robot-builds/<id>` | Owner or admin | Returns one `robot_build`. |
| PATCH | `/robot-builds/<id>` | Owner or admin | Edit name, description, or stage. Send a null description to clear it. |
| DELETE | `/robot-builds/<id>` | Owner or admin | Deletes the build (204, empty body). |

Email and build names are trimmed and accept 1–255 characters. Emails are case-sensitive. Passwords accept 8–128 characters. The service assigns ownership from the authenticated account and rejects attempts to set or transfer ownership in build requests.

Errors carry an `error` object with `code` and `message`. Validation errors include `fields` (400). Authentication failures return 401, a regular user at the admin endpoint gets 403, and an unavailable build returns 404, including when another user owns it. Duplicate email returns 409.

### Try a build

In a second shell, use a disposable local account.

```sh
base=http://127.0.0.1:5050
creds='{"email":"developer@example.com","password":"local-demo-password"}'
curl -sS -X POST "$base/registration" -H 'Content-Type: application/json' -d "$creds"
token=$(curl -sS -X POST "$base/login" -H 'Content-Type: application/json' -d "$creds" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -sS "$base/me" -H "Authorization: Bearer $token"
curl -sS -X POST "$base/robot-builds" -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' -d '{"name":"Line follower","description":"Dual infrared sensors"}'
curl -sS "$base/robot-builds" -H "Authorization: Bearer $token"
```

## Tests

```sh
source .venv/bin/activate
python -m pytest -q
```

Each test migrates a temporary SQLite database. Coverage includes password hashing, authentication, role changes, two-user isolation, admin access, build ownership, and database constraints.

## Scope

This tracker runs locally. Tokens expire after the configured lifetime. There is no refresh or logout endpoint. The build list is unpaginated, and the development server is intended for local use.
