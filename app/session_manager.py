import time
from collections import defaultdict

class SessionManager:
    def __init__(self, timeout: int = 3600):
        # token -> session_data (dict)
        self.tokens: dict[str, dict] = {}

        # user_id -> set of tokens
        self.tokens_by_id: dict[str, set[str]] = defaultdict(set)

        self.timeout = timeout

    # --- Session Management ---
    
    def create_session(self, token: str, user_id: str):
        now = time.time()
        self.tokens[token] = {
            "user_id": user_id,
            "flags": [],
            "expiry": now + self.timeout
        }
        self.tokens_by_id[user_id].add(token)

    def close_session_for_token(self, token: str):
        session = self.tokens.pop(token, None)
        if session:
            user_id = session["user_id"]
            self.tokens_by_id[user_id].discard(token)
            if not self.tokens_by_id[user_id]:
                del self.tokens_by_id[user_id]

    def close_sessions_for_id(self, user_id: str):
        tokens = self.tokens_by_id.pop(user_id, set())
        for token in tokens:
            self.tokens.pop(token, None)

    def extend_session(self, token: str):
        if token in self.tokens:
            self.tokens[token]["expiry"] = time.time() + self.timeout

    def is_session_active(self, token: str) -> bool:
        return token in self.tokens and self.tokens[token]["expiry"] > time.time()

    # --- Flag Management ---
    
    def session_has_flag(self, token: str, flag: str) -> bool:
        return token in self.tokens and flag in self.tokens.get(token, {}).get("flags", [])

    def get_flags_by_token(self, token: str) -> list:
        return self.tokens.get(token, {}).get("flags", [])

    def get_flags_by_id(self, user_id: str) -> dict:
        """Returns a dict of {token: flags} for all active sessions of the user."""
        result = {}
        for token in self.tokens_by_id.get(user_id, set()):
            result[token] = self.get_flags_by_token(token)
        return result

    def add_flag_by_token(self, token: str, flag: str):
        if token in self.tokens and flag not in self.tokens[token]["flags"]:
            self.tokens[token]["flags"].append(flag)

    def remove_flag_by_token(self, token: str, flag: str):
        if token in self.tokens and flag in self.tokens[token]["flags"]:
            self.tokens[token]["flags"].remove(flag)

    def add_flag_by_id(self, user_id: str, flag: str):
        for token in self.tokens_by_id.get(user_id, set()):
            self.add_flag_by_token(token, flag)

    def remove_flag_by_id(self, user_id: str, flag: str):
        for token in self.tokens_by_id.get(user_id, set()):
            self.remove_flag_by_token(token, flag)
