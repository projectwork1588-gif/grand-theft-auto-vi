"""Consistent error handling: JSON for /api/*, a styled HTML page for everything else."""
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from .db import DatabaseError
from .services.validation import ValidationError


def _wants_json():
    return request.path.startswith("/api/")


def _respond(status, title, message, details=None):
    if _wants_json():
        body = {"error": {"status": status, "title": title, "message": message}}
        if details:
            body["error"]["details"] = details
        return jsonify(body), status
    return render_template("error.html", status=status, title=title, message=message, details=details), status


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(error):
        return _respond(400, "Bad request", "Some of the values in the address were not valid.", error.problems)

    @app.errorhandler(HTTPException)
    def handle_http(error):
        return _respond(error.code, error.name, error.description)

    @app.errorhandler(DatabaseError)
    def handle_database(error):
        app.logger.exception("Database error: %s", error)
        # Do not leak SQL or credentials to the visitor.
        return _respond(503, "Database unavailable", "The database could not be reached. Please try again shortly.")

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        app.logger.exception("Unhandled error: %s", error)
        return _respond(500, "Server error", "Something went wrong on our side.")
