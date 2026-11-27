"""Implementación concreta de PasswordHasher usando bcrypt."""
import bcrypt

from src.domain.repositories import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def __init__(self, rounds: int = 12):
        self.rounds = rounds

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=self.rounds)).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False
