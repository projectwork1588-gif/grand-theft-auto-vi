"""Entry point: `python -m flask --app wsgi run` (or any WSGI server).

The configuration comes from FLASK_ENV. When it is not set, only the Flask command line (the documented local run) falls back to development; any other
server refuses to start, so a deployment that forgot FLASK_ENV=production cannot quietly run with development settings (see deployment_config_name)."""
from app import create_app
from app.config import deployment_config_name   # importing app.config has already read .env

app = create_app(deployment_config_name())
