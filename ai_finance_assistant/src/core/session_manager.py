from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
import sqlite3
import json
import os


@dataclass
class UserProfile:
    user_id: str
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    investment_horizon: str = "medium"  # short (1-3yr), medium (3-10yr), long (10yr+)
    experience_level: str = "beginner"  # beginner, intermediate, advanced
    created_at: float = field(default_factory=time.time)


@dataclass
class ConversationTurn:
    role: str
    content: str
    agent: str
    timestamp: float = field(default_factory=time.time)


class SessionManager:
    def __init__(self, db_path: Optional[str] = None):
        """If db_path is provided, persist sessions to a local SQLite database.

        Otherwise use in-memory sessions (original behavior).
        """
        self._sessions: Dict[str, Dict] = {}
        self.db_path = db_path
        if db_path:
            # ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self._init_db()

    def get_or_create_session(self, session_id: str) -> Dict:
        if self.db_path:
            # load from DB or create
            row = self._fetch_profile(session_id)
            if not row:
                profile = UserProfile(user_id=session_id)
                self._save_profile(session_id, profile)
                history = []
                portfolio = None
            else:
                profile = UserProfile(
                    user_id=row[0],
                    risk_tolerance=row[1] or "moderate",
                    investment_horizon=row[2] or "medium",
                    experience_level=row[3] or "beginner",
                    created_at=row[4] or time.time(),
                )
                history = self._fetch_history(session_id)
                portfolio = self._fetch_portfolio(session_id)

            self._sessions[session_id] = {"profile": profile, "history": history, "portfolio": portfolio}
            return self._sessions[session_id]

        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "profile": UserProfile(user_id=session_id),
                "history": [],
                "portfolio": None,
            }
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str, agent: str = "system"):
        session = self.get_or_create_session(session_id)
        turn = ConversationTurn(role=role, content=content, agent=agent)
        session["history"].append(turn)
        if self.db_path:
            self._save_history_entry(session_id, turn)

    def get_history(self, session_id: str, last_n: int = 10) -> List[Dict]:
        session = self.get_or_create_session(session_id)
        turns = session["history"][-last_n:]
        return [{"role": t.role, "content": t.content} for t in turns]

    def update_portfolio(self, session_id: str, portfolio: Dict):
        session = self.get_or_create_session(session_id)
        session["portfolio"] = portfolio
        if self.db_path:
            self._save_portfolio(session_id, portfolio)

    def get_portfolio(self, session_id: str) -> Optional[Dict]:
        session = self.get_or_create_session(session_id)
        return session.get("portfolio")

    def update_profile(self, session_id: str, **kwargs):
        session = self.get_or_create_session(session_id)
        for k, v in kwargs.items():
            if hasattr(session["profile"], k):
                setattr(session["profile"], k, v)
        if self.db_path:
            self._save_profile(session_id, session["profile"])

    def get_profile(self, session_id: str) -> UserProfile:
        session = self.get_or_create_session(session_id)
        return session["profile"]

    # --- SQLite helpers ---
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY,
                risk_tolerance TEXT,
                investment_horizon TEXT,
                experience_level TEXT,
                created_at REAL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                agent TEXT,
                timestamp REAL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolios (
                user_id TEXT PRIMARY KEY,
                portfolio_json TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def _fetch_profile(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT user_id, risk_tolerance, investment_horizon, experience_level, created_at FROM profiles WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def _save_profile(self, user_id: str, profile: UserProfile):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO profiles (user_id, risk_tolerance, investment_horizon, experience_level, created_at) VALUES (?, ?, ?, ?, ?)",
            (profile.user_id, profile.risk_tolerance, profile.investment_horizon, profile.experience_level, profile.created_at),
        )
        conn.commit()
        conn.close()

    def _save_history_entry(self, user_id: str, turn: ConversationTurn):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO history (user_id, role, content, agent, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, turn.role, turn.content, turn.agent, turn.timestamp),
        )
        conn.commit()
        conn.close()

    def _fetch_history(self, user_id: str, last_n: int = 100):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content, agent, timestamp FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, last_n)
        )
        rows = cur.fetchall()
        conn.close()
        # return in chronological order
        rows = list(reversed(rows))
        return [ConversationTurn(role=r[0], content=r[1], agent=r[2], timestamp=r[3]) for r in rows]

    def _save_portfolio(self, user_id: str, portfolio: Dict):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO portfolios (user_id, portfolio_json) VALUES (?, ?)",
            (user_id, json.dumps(portfolio)),
        )
        conn.commit()
        conn.close()

    def _fetch_portfolio(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT portfolio_json FROM portfolios WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None
