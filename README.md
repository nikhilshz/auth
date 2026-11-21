# Authentication API

## Run locally

Requires Python 3.14 or newer and `uv`.

1. Install dependencies with `uv sync`.
2. Set `JWT_SECRET_KEY` in the root `.env` file.
3. Start the development server from the repository root:

	 ```powershell
	 uv run fastapi dev app/main.py
	 ```

The API documentation is available at `/docs`. The SQLite database is created as
`auth.db` in the working directory on startup.

## Project layout

```text
app/
	api/
		dependencies.py
		routes/
			auth.py
			password_reset.py
			users.py
	core/
		config.py
		security.py
	db/
		session.py
	main.py
	models.py
	schemas.py
```

Route modules own HTTP endpoints, `models.py` contains database tables, and
`schemas.py` contains request and response models.
