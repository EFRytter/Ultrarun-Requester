# Ultrarun Requester

Author: EFRytter 
Project: Ultrarun-Requester
License: MIT (choose a license you prefer and update this section)

Overview
--------
This is a small Flask web application that helps endurance event teams coordinate food, drink and other supplies at aid stations during a run. Team members (crew) can create runs and stations; runners can select which items they want at each station; crew can view those selections and prepare accordingly.

Why this README exists
-----------------------
This README explains what the project does, how to set up a development environment, how to run the app locally, where to find important files, and how to contribute or extend the project.

Quick start (development)
-------------------------
1. Create and activate a virtual environment (recommended):

	Windows (PowerShell):
	```powershell
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	pip install -r requirements.txt
	```

	macOS / Linux:
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt
	```

2. Initialize the database and start the server:

	```bash
	python app.py
	```

	The app will create the SQLite database under the `instance/` folder and start a development server at `http://127.0.0.1:5000` by default.

Running tests and helpers
-------------------------
- `render_home_test.py`: helper script to render templates without running the full server (useful to check template errors).
- `inspect_db.py` / `inspect_instance_db.py`: small helpers to inspect the SQLite files.
- `test_add_run.py`: simple integration-style checks (not a full test-suite).

Project layout
--------------
- `app.py` — Main Flask application, routes, and SQLAlchemy models.
- `templates/` — Jinja2 templates for pages: `base.html`, `home.html`, `station.html`, `addevent.html`, `addstation.html`, `login.html`, `profile.html`, `register.html`.
- `static/` — Static assets including `style.css`, `images/`, and uploaded item images under `static/uploads`.
- `instance/` — Holds runtime instance files, including SQLite DB files.
- `requirements.txt` — Python package dependencies for development and running the app.

Important details
-----------------
- The app uses Flask + SQLAlchemy and stores data in SQLite for simplicity. For production use, consider PostgreSQL and proper migrations (Flask-Migrate / Alembic).
- The app stores uploaded images in `static/uploads`. Filenames are sanitized with `werkzeug.utils.secure_filename`.
- Team authentication is basic: users are `Team` records with a password hash. Current code uses `session['team_id']` for scoping `Item`s; improve authentication before public deployment.
- Database schema changes are applied via `db.create_all()` at startup. If you need safe upgrades, add migration tooling.

How to contribute
-----------------
1. Fork the repository and create a feature branch.
2. Make changes and add tests where appropriate.
3. Open a pull request with a clear description of the change and why it is needed.

Suggested improvements
----------------------
- Add edit/delete for Items and StationItems from the UI.
- Extract inline JavaScript and CSS into static files for caching and maintainability.
- Add proper user registration/login flows and permissions.
- Replace periodic polling with WebSocket-based live updates for real-time sync.
- Add database migrations and deploy to a hosted database for production.

Contact / Author
----------------
Project maintained by EFRytter. For questions or help, open an issue on the project repository.

License
-------
This project is provided under the MIT license, or change to any license you prefer. Update this section to reflect the chosen license file.
