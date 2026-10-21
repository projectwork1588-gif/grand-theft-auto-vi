"""Registration, sign-in and password change: the rules. No Flask request handling and no SQL here (see repositories/users.py).

Passwords are hashed with Werkzeug's scrypt (a maintained, memory-hard hash with a random salt per password); no plaintext is stored or logged.
"""
import re

import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

from ..repositories import users as users_repo

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")
PASSWORD_MIN, PASSWORD_MAX = 10, 128           # the maximum stops a huge input from being used to burn the server's time in the hash
HASH_METHOD = "scrypt"
DUPLICATE_ENTRY = 1062

GENERIC_LOGIN_ERROR = "That username and password do not match."


class FormError(Exception):
    """Raised with {field: message} (field "" is a message about the whole form) and the HTTP status the page should answer with."""

    def __init__(self, errors, status=400):
        super().__init__("form not accepted")
        self.errors = errors
        self.status = status


_dummy_hash = None


def hash_password(password):
    return generate_password_hash(password, method=HASH_METHOD)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def _burn_a_hash(password):
    """Check against a throwaway hash so an unknown username takes about as long as a wrong password (no timing clue about which usernames exist)."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("not-a-real-account-password")
    verify_password(_dummy_hash, password)


def normalise_username(raw):
    return (raw or "").strip().lower()


def check_username(username):
    if not USERNAME_PATTERN.match(username):
        return "Use 3 to 30 characters: lowercase letters, numbers and underscores."
    return None


def check_new_password(password, username=""):
    if len(password) < PASSWORD_MIN:
        return f"Use at least {PASSWORD_MIN} characters."
    if len(password) > PASSWORD_MAX:
        return f"Use at most {PASSWORD_MAX} characters."
    if "\x00" in password:
        return "That password contains a character that is not allowed."
    if username and password.lower() == username:
        return "The password must not be the same as the username."
    return None


def register(form):
    """Create an account from a submitted form and return the new user row. Raises FormError (400 invalid, 409 username taken)."""
    username = normalise_username(form.get("username"))
    password = form.get("password") or ""
    confirm = form.get("password_confirm") or ""
    errors = {}
    problem = check_username(username)
    if problem:
        errors["username"] = problem
    problem = check_new_password(password, username)
    if problem:
        errors["password"] = problem
    elif password != confirm:
        errors["password_confirm"] = "The two passwords are not the same."
    if errors:
        raise FormError(errors, 400)
    try:
        user_id = users_repo.create(username, hash_password(password))
    except mysql.connector.IntegrityError as error:
        if error.errno == DUPLICATE_ENTRY:
            raise FormError({"username": "That username is already taken."}, 409)
        raise
    return users_repo.get_by_id(user_id)


def authenticate(form):
    """Return the user row for a correct username and password, else None. The caller shows one message for both failures (GENERIC_LOGIN_ERROR)."""
    username = normalise_username(form.get("username"))
    password = form.get("password") or ""
    if not username or not password or len(password) > PASSWORD_MAX or len(username) > 30:
        return None
    user = users_repo.get_by_username(username)
    if user is None:
        _burn_a_hash(password)
        return None
    return user if verify_password(user["password_hash"], password) else None


def change_password(user, form):
    """Replace the password after checking the current one. Raises FormError. Returns the user row as it is stored afterwards."""
    current = form.get("current_password") or ""
    new = form.get("new_password") or ""
    confirm = form.get("new_password_confirm") or ""
    stored = users_repo.get_by_id(user["user_id"])
    errors = {}
    if stored is None or not current or len(current) > PASSWORD_MAX or not verify_password(stored["password_hash"], current):
        errors["current_password"] = "That is not your current password."
    else:
        problem = check_new_password(new, stored["username"])
        if problem:
            errors["new_password"] = problem
        elif new == current:
            errors["new_password"] = "Choose a password you are not already using."
        elif new != confirm:
            errors["new_password_confirm"] = "The two passwords are not the same."
    if errors:
        raise FormError(errors, 400)
    users_repo.update_password(stored["user_id"], hash_password(new))
    return users_repo.get_by_id(stored["user_id"])
