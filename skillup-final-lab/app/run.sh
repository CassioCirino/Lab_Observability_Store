#!/usr/bin/env bash
export DATABASE_FILE=${DATABASE_FILE:-./db/skillup.db}
export FLASK_APP=app.app:app
/opt/skillup-final-lab/venv/bin/python3 -m gunicorn --bind 0.0.0.0:8080 app.app:app
