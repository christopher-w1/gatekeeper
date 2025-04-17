from hashlib import sha256
from os import urandom
import re


def hash_password(password: str, salt: str):
    """
    Hashes the password, salts it, then hashes it again.
    """
    if not salt:
        salt = generate_salt()
    first_hash = sha256(password.encode('utf-8')).hexdigest()
    hasher = sha256()
    hasher.update((first_hash + salt).encode('utf-8'))
    hashcode = hasher.hexdigest()
    return f"$SHA${salt}${hashcode}"


def generate_salt(length=16):
    """
    Generate a random hexadecimal string of a given length
    """
    return urandom((length+1)//2).hex()[:length]


def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verifies the password against the stored hash.
    """
    try:
        _, salt, hashcode = stored_hash.split('$')
        return hash_password(password, salt) == stored_hash
    except ValueError:
        return False  # Invalid hash format


def is_valid_password(password: str) -> bool:
    """
    Password must be at least 7 characters, include one uppercase letter,
    one lowercase letter and one digit.
    """
    if len(password) < 7:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


def is_valid_email(email: str) -> bool:
    """
    Very simple email validation.
    """
    email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
    return bool(email_regex.match(email))


def is_valid_username(username: str) -> bool:
    """
    Username must be 3-32 characters, only alphanumerics and underscores.
    """
    return bool(re.fullmatch(r"^[A-Za-z0-9_]{3,32}$", username))
