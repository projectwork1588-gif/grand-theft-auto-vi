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
    if request.method != "POST":
        return _page("account/register.html", errors={}, values={})
    wait, ticket = security.begin_registration()                 # check and reserve in one step: simultaneous sign-ups cannot all pass the check
    if wait:
        return _too_many("account/register.html", wait, "accounts created from this address", values={})
    try:
        user = accounts.register(request.form)
    except accounts.FormError as error:
        if error.status == 409:                                  # it got as far as the hash and the INSERT, which is what the limit is for
            security.settle_attempt(ticket)
        else:                                                    # an invalid form costs nothing
            security.release_attempt(ticket)
        return _page("account/register.html", error.status, errors=error.errors, values={"username": accounts.normalise_username(request.form.get("username"))[:30]})
    except BaseException:                                        # a database or other server error: this sign-up never happened
        security.release_attempt(ticket)
        raise
    security.settle_attempt(ticket)
    security.sign_in(user)
    flash("Your account is ready. You are signed in.", "success")
    return _to("account.favourites_page")


@account_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return _to("account.favourites_page")
    if request.method != "POST":
        return _page("account/login.html", errors={}, values={})
    username = accounts.normalise_username(request.form.get("username"))
    wait, ticket = security.begin_login_attempt(username)        # check and reserve in one step, BEFORE the (slow) password check
    if wait:
        return _too_many("account/login.html", wait, values={"username": username[:30]})
    try:
        user = accounts.authenticate(request.form)
    except BaseException:                                        # a database or other server error: this attempt never happened
        security.release_attempt(ticket)
        raise
    if user is None:
        security.settle_attempt(ticket)                          # a wrong password or an unknown name: it counts
        return _page("account/login.html", 401, errors={"": accounts.GENERIC_LOGIN_ERROR}, values={"username": username[:30]})
    security.login_succeeded(ticket, username)                   # a success consumes nothing from the failed-attempt budget
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
    if request.method != "POST":
        return _page("account/password.html", errors={})
    username = g.user["username"]
    wait, ticket = security.begin_login_attempt(username)        # the "current password" field is a password check, held to the same limits as sign-in
    if wait:
        return _too_many("account/password.html", wait)
    try:
        user = accounts.change_password(g.user, request.form)
    except accounts.FormError as error:
        if "current_password" in error.errors:
            security.settle_attempt(ticket)                      # a wrong current password is a guess: it counts
        else:
            security.release_attempt(ticket)                     # the current password was right; a weak or mismatched NEW password is not a guess
        return _page("account/password.html", error.status, errors=error.errors)
    except BaseException:                                        # a database or other server error: this attempt never happened
        security.release_attempt(ticket)
        raise
    security.login_succeeded(ticket, username)
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
