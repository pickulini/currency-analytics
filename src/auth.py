import json
import hashlib
import os

class AuthManager:
    def __init__(self, users_file="data/users.json"):
        self.users_file = users_file
        self.current_user = None
        self._ensure_users_file()

    def _ensure_users_file(self):
        if not os.path.exists(self.users_file):
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            admin_hash = hashlib.sha256("admin".encode()).hexdigest()
            default_users = {
                "admin": {
                    "password_hash": admin_hash,
                    "role": "admin",
                    "reports_folder": "data/reports/admin"
                }
            }
            with open(self.users_file, "w") as f:
                json.dump(default_users, f, indent=4)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        if not os.path.exists(self.users_file):
            return False, None
        with open(self.users_file, "r") as f:
            users = json.load(f)
        if username in users:
            if users[username]["password_hash"] == self._hash_password(password):
                self.current_user = {
                    "username": username,
                    "role": users[username]["role"],
                    "reports_folder": users[username]["reports_folder"]
                }
                return True, users[username]["role"]
        return False, None

    def register(self, username, password):
        if not username or not password:
            return False, "Логин и пароль не могут быть пустыми"
        with open(self.users_file, "r") as f:
            users = json.load(f)
        if username in users:
            return False, "Пользователь с таким логином уже существует"
        users[username] = {
            "password_hash": self._hash_password(password),
            "role": "user",
            "reports_folder": f"data/reports/{username}"
        }
        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=4)
        os.makedirs(f"data/reports/{username}", exist_ok=True)
        return True, "Регистрация успешна"

    def get_current_user(self):
        return self.current_user

    def logout(self):
        self.current_user = None

    def list_users(self):
        if not os.path.exists(self.users_file):
            return []
        with open(self.users_file, "r") as f:
            users = json.load(f)
        return [{"username": u, "role": users[u]["role"]} for u in users]
