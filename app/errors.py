"""Consistent error handling: JSON for /api/*, a branded HTML page for everything else."""
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException, MethodNotAllowed

from .db import DatabaseError
from .services.validation import ValidationError

# What the branded page says for the statuses a visitor can really meet: (headline, sentence under it). The <title>, the JSON body and any message
# a route chose itself (abort(403, "...")) are left as they were; only Werkzeug's stock sentences are replaced on the page.
BRANDED = {
    404: ("Off the map", "We could not find that page. It may have moved, or the address may have a typo."),
    403: ("Restricted area", "You do not have permission to open this page."),
    405: ("Wrong turn", "This address does not accept that kind of request."),
    500: ("Something broke on our side", "We hit a problem and it has been logged. Try again in a moment."),
    503: ("Back in a moment", "The site could not reach its data just now. Please try again shortly."),
}
RETRY = {500, 503}


def _wants_json():
    return request.path.startswith("/api/")


def _retry_url():
    """Where "Try again" goes: this same path, for a GET only, and never an address that could point off the site."""
    path = request.path
    if request.method == "GET" and path.startswith("/") and not path.startswith("//"):
        return path
    return None


def _respond(status, title, message, details=None, own_message=False, headers=None):
    """`own_message` is True when the route chose the sentence itself, so the page keeps it instead of the branded one. `headers` are added to the answer (a 405 must say what is allowed)."""
    if _wants_json():
        body = {"error": {"status": status, "title": title, "message": message}}
        if details:
            body["error"]["details"] = details
        return jsonify(body), status, headers or {}
    headline, lede = BRANDED.get(status, (title, message))
    if own_message:
        lede = message
    retry = _retry_url() if status in RETRY else None
    return render_template("error.html", status=status, title=title, headline=headline, message=lede, details=details, retry_url=retry), status, headers or {}


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(error):
        return _respond(400, "Bad request", "Some of the values in the address were not valid.", error.problems)

    @app.errorhandler(HTTPException)
    def handle_http(error):
        headers = {"Allow": ", ".join(sorted(error.valid_methods))} if isinstance(error, MethodNotAllowed) and error.valid_methods else None      # RFC 9110: a 405 lists what is allowed
        return _respond(error.code, error.name, error.description, own_message=error.description != type(error).description, headers=headers)

    @app.errorhandler(DatabaseError)
    def handle_database(error):
        app.logger.exception("Database error: %s", error)
        # Do not leak SQL or credentials to the visitor.
        return _respond(503, "Database unavailable", "The database could not be reached. Please try again shortly.")

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        app.logger.exception("Unhandled error: %s", error)
        return _respond(500, "Server error", "Something went wrong on our side.")
