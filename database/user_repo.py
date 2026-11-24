import os
import hashlib
import hmac
import sqlite3


class UserRepository:
    def __init__(self, db_conn):
        self._conn = db_conn

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return f"pbkdf2_sha256${salt.hex()}${key.hex()}"

    @staticmethod
    def verify_password(stored_hash: str, provided_password: str) -> bool:
        """Verifies a plaintext password against a stored PBKDF2 hash in constant time."""
        try:
            algorithm, salt_hex, key_hex = stored_hash.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            provided_key = hashlib.pbkdf2_hmac(
                "sha256", provided_password.encode("utf-8"), salt, 100_000
            )
            return hmac.compare_digest(expected_key, provided_key)
        except (ValueError, TypeError):
            return False

    def create_user(self, username: str, password: str, role: str) -> tuple[bool, str]:
        clean_username = username.strip()
        clean_role = role.strip().capitalize()

        if clean_role not in ("Admin", "Staff"):
            return False, "Invalid account role. Must be Admin or Staff."
        if len(clean_username) < 3:
            return False, "Username must be at least 3 characters long."
        if " " in clean_username:
            return False, "Username cannot contain spaces."
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."

        hashed_pw = self.hash_password(password)
        try:
            with self._conn.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (clean_username, hashed_pw, clean_role),
                )
                conn.commit()
            return True, f"{clean_role} account '{clean_username}' created successfully."
        except sqlite3.IntegrityError:
            return False, f"Username '{clean_username}' is already taken."
        except sqlite3.Error as e:
            return False, f"Database error ({self._conn.db_path}): {e}"

    def authenticate_user(self, username: str, password: str) -> str | None:
        with self._conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, password_hash, role FROM users WHERE username = ?",
                (username.strip(),),
            )
            user = cursor.fetchone()

        if user and self.verify_password(user["password_hash"], password):
            return user["role"]
        return None