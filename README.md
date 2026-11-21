# FastAPI Authentication

A small FastAPI authentication API with JWT access and refresh tokens, logout invalidation, password reset, and SQLite persistence.

## Features

- User registration and login
- Access and refresh tokens
- Protected `/me` and dashboard routes
- Session-based logout revocation
- Password reset request and confirmation
- Argon2 password hashing
- Automatic Swagger and ReDoc API documentation

## Requirements

- Python 3.14+
- `uv`

## Setup

1. Install dependencies:

```powershell
uv sync
```

2. Create a `.env` file in the project root:

```env
JWT_SECRET_KEY=replace-this-with-a-long-random-secret
```

Generate a secret with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The SQLite database is created automatically as `auth.db` on startup.

## Main Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/register` | Register a user |
| `POST` | `/token` | Log in and receive tokens |
| `POST` | `/token/refresh` | Create a new access token |
| `POST` | `/logout` | Revoke the current login session |
| `GET` | `/me` | Get the authenticated user |
| `PATCH` | `/me` | Update the authenticated user's email |
| `GET` | `/dashboard` | Protected example route |
| `POST` | `/password-reset/request` | Request a password reset |
| `POST` | `/password-reset/confirm` | Confirm a password reset |


Routes are organized by feature, database tables live in `models.py`, request and response models live in `schemas.py`, and shared JWT/password utilities live in `app/core`.
