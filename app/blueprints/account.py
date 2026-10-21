"""Accounts and favourites: register, sign in, sign out, change password, and save/unsave a character, vehicle, place or story.

Every state-changing route is a POST that passes the CSRF check in app/security.py. The signed-in user comes from the session only; no route takes a
user id, a role or a redirect address from the request.
"""
from flask import Blueprint, flash, g, make_response, redirect, render_template, request, url_for

from .. import security
from ..repositories.favourites import KINDS
from ..services import accounts, favourites
from ..services.validation import require_slug

account_bp = Blueprint("account", __name__)


def _to(endpoint, **values):
    return redirect(url_for(endpoint, **values), code=303)       # 303: the browser follows a POST with a GET, so a refresh does not repeat the action


def _page(template, status=200, headers=None, **context):
    response = make_response(render_template(template, **context), status)
    response.headers.update(headers or {})
    return response


def _too_many(template, wait, what="failed attempts", **context):
    minutes = max(1, -(-wait // 60))
    return _page(template, 429, {"Retry-After": str(wait)}, errors={"": f"Too many {what}. Try again in {minutes} minute(s)."}, **context)


# ------------------------------------------------------------------ register / sign in / sign out
@account_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return _to("account.favourites_page")
    if request.method == "GET":
        return _page("account/register.html", errors={}, values={})
    wait = security.register_blocked_for()
    if wait:
        return _too_many("account/register.html", wait, "accounts created from this address", values={})
    try:
        user = accounts.register(request.form)
    except accounts.FormError as error:
        if error.status == 409:                      # it got as far as the hash and the INSERT, which is what the limit is for; an invalid form costs nothing
            security.record_registration()
        return _page("account/register.html", error.status, errors=error.errors, values={"username": accounts.normalise_username(request.form.get("username"))[:30]})
    security.record_registration()
    security.sign_in(user)
    flash("Your account is ready. You are signed in.", "success")
    return _to("account.favourites_page")


@account_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return _to("account.favourites_page")
    if request.method == "GET":
        return _page("account/login.html", errors={}, values={})
    username = accounts.normalise_username(request.form.get("username"))
    wait = security.login_blocked_for(username)
    if wait:
        return _too_many("account/login.html", wait, values={"username": username[:30]})
    user = accounts.authenticate(request.form)
    if user is None:
        security.record_login_failure(username)
        return _page("account/login.html", 401, errors={"": accounts.GENERIC_LOGIN_ERROR}, values={"username": username[:30]})
    security.clear_login_failures(username)
    security.sign_in(user)
    flash("You are signed in.", "success")
    return _to("account.favourites_page")


@account_bp.post("/logout")
def logout():
    security.sign_out()
    flash("You have been signed out.", "info")
    return _to("main.index")


# ------------------------------------------------------------------ change password
@account_bp.route("/account/password", methods=["GET", "POST"])
@security.login_required
def password():
    if request.method == "GET":
        return _page("account/password.html", errors={})
    username = g.user["username"]
    wait = security.login_blocked_for(username)
    if wait:
        return _too_many("account/password.html", wait)
    try:
        user = accounts.change_password(g.user, request.form)
    except accounts.FormError as error:
        if "current_password" in error.errors:
            security.record_login_failure(username)
        return _page("account/password.html", error.status, errors=error.errors)
    security.clear_login_failures(username)
    security.sign_in(user)             # a new session for this browser; every other browser's session no longer matches the new password
    flash("Your password has been changed.", "success")
    return _to("account.favourites_page")


# ------------------------------------------------------------------ favourites
@account_bp.get("/account/favourites")
@security.login_required
def favourites_page():
    groups = favourites.overview(g.user["user_id"])
    return render_template("account/favourites.html", groups=groups, total=sum(len(group["items"]) for group in groups))


def _back(kind, slug):
    """Where to go after saving or removing: the favourites list when the button was pressed there, otherwise the record's own page. Both are fixed by the server."""
    if request.form.get("return") == "list":
        return _to("account.favourites_page")
    return _to(KINDS[kind][5], slug=slug)


@account_bp.post("/favourites/<kind>/<slug>")
@security.login_required
def save_favourite(kind, slug):
    favourites.kind_or_404(kind)
    require_slug(slug)
    name = favourites.save(g.user["user_id"], kind, slug)
    flash(f"{name} is saved to your favourites.", "success")
    return _back(kind, slug)


@account_bp.post("/favourites/<kind>/<slug>/remove")
@security.login_required
def remove_favourite(kind, slug):
    favourites.kind_or_404(kind)
    require_slug(slug)
    name = favourites.unsave(g.user["user_id"], kind, slug)
    flash(f"{name} is removed from your favourites.", "info")
    return _back(kind, slug)
