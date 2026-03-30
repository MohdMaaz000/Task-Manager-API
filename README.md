44# Task Manager API

Production-style REST API for task management built with Python, Flask, SQLAlchemy, JWT authentication, and automated tests.

## Repository

- GitHub: `https://github.com/MohdMaaz000/Task-Manager-API`
- Maintainer: `Mohd Maaz`

## Highlights

- User registration and login with JWT access and refresh tokens
- Protected task CRUD endpoints
- Task filtering, search, stats, bulk-complete, and clear-completed actions
- Request validation and safer JSON error handling
- Rate limiting for sensitive endpoints
- Environment-based configuration
- Automated API tests using `unittest`
- Ready to run behind `waitress` or another WSGI server

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-Limiter
- SQLite by default, PostgreSQL-ready through `DATABASE_URL`

## Project Structure

- `app.py`: app factory, root routes, JWT handlers, error handling
- `auth.py`: authentication blueprint
- `tasks.py`: task blueprint
- `models.py`: SQLAlchemy models
- `config.py`: environment-aware settings
- `validators.py`: request payload validation
- `tests/test_api.py`: automated API smoke and behavior tests
- `wsgi.py`: WSGI entrypoint

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`
- `JWT_REFRESH_TOKEN_EXPIRES_DAYS`
- `RATELIMIT_STORAGE_URI`
- `CORS_ORIGINS`
- `LOG_LEVEL`
- `CREATE_DB_ON_STARTUP`

## Local Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API will start on `http://127.0.0.1:5000`.

## Run Tests

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```

## GitHub Upload Checklist

This repository is prepared for public upload:

- `.env` is ignored through `.gitignore`
- `.env.example` is included for setup guidance
- local SQLite files and virtual environments are ignored
- GitHub Actions CI is included in `.github/workflows/tests.yml`

Before pushing, make sure:

1. Your real `.env` file is not committed
2. Your secrets are changed from placeholder values
3. Your repository name and description are set clearly on GitHub

Example git commands:

```powershell
git init
git add .
git commit -m "Initial production-style Task Manager API"
git branch -M main
git remote add origin https://github.com/MohdMaaz000/Task-Manager-API.git
git push -u origin main
```

## Main Endpoints

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /refresh`

### Tasks

- `POST /tasks`
- `GET /tasks`
- `GET /tasks/<id>`
- `PUT /tasks/<id>`
- `DELETE /tasks/<id>`
- `PATCH /tasks/<id>/toggle`
- `PATCH /tasks/complete-all`
- `DELETE /tasks/clear-completed`
- `GET /tasks/stats`

### System

- `GET /`
- `GET /health`
- `GET /dashboard`

## Example Request

`POST /tasks`

```json
{
  "title": "Prepare project documentation",
  "priority": "HIGH",
  "due_date": "2026-04-15"
}
```

Header:

```text
Authorization: Bearer <access_token>
```

## Query Parameters

- `page`
- `limit`
- `completed=true|false`
- `search=keyword`

## Production Notes

- Replace the example secrets in `.env` before deployment.
- Use PostgreSQL in production instead of SQLite.
- Set `CORS_ORIGINS` to your frontend domain instead of `*`.
- Use a persistent rate-limit backend such as Redis by changing `RATELIMIT_STORAGE_URI`.
- Run the app with a production WSGI server such as `waitress`.

## Deployment

This project is prepared for deployment with:

- `wsgi.py` as the WSGI entrypoint
- `Procfile` for platform process startup
- `runtime.txt` for Python version pinning
- `render.yaml` for one-click Render-style deployment
- `Dockerfile` for container-based deployment

### Deploy on Render

1. Push the repository to GitHub
2. Create a new Web Service on Render
3. Connect the GitHub repository
4. Render can detect `render.yaml`, or you can set these manually:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn wsgi:app`
- Health check path: `/health`

5. Add environment variables:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`
- `JWT_REFRESH_TOKEN_EXPIRES_DAYS`
- `RATELIMIT_STORAGE_URI`
- `CORS_ORIGINS`
- `LOG_LEVEL`
- `CREATE_DB_ON_STARTUP`

### Recommended Production Upgrade

For the strongest deployment story, use:

- PostgreSQL instead of SQLite
- Redis-backed rate limiting instead of in-memory limits
- restricted CORS origins instead of `*`
- generated secrets from your hosting platform

### Run with Docker

```powershell
docker build -t task-manager-api .
docker run -p 8000:8000 --env-file .env task-manager-api
```

## Resume Pitch

Built a production-oriented Task Manager REST API using Python and Flask with JWT authentication, SQLAlchemy ORM, rate limiting, input validation, automated tests, and deployable environment-based configuration.
