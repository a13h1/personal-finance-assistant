from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time
import json
import os
import logging

from sqlalchemy import create_engine, Column, String, Float, Text, Integer, Index
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError
from contextlib import contextmanager

logger = logging.getLogger(__name__)

Base = declarative_base()


class UserRecord(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True)
    risk_tolerance = Column(String(20), default="moderate")
    investment_horizon = Column(String(20), default="medium")
    experience_level = Column(String(20), default="beginner")
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)


class HistoryRecord(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    agent = Column(String(50), default="system")
    timestamp = Column(Float, default=time.time)

    __table_args__ = (Index("ix_history_user_id", "user_id"),)


class PortfolioRecord(Base):
    __tablename__ = "portfolio_holdings"

    user_id = Column(String(36), primary_key=True)
    portfolio_json = Column(Text, nullable=False)
    updated_at = Column(Float, default=time.time)


class SessionRecord(Base):
    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    created_at = Column(Float, default=time.time)

    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)


@dataclass
class UserProfile:
    user_id: str
    risk_tolerance: str = "moderate"   # conservative | moderate | aggressive
    investment_horizon: str = "medium"  # short (1-3yr) | medium (3-10yr) | long (10yr+)
    experience_level: str = "beginner"  # beginner | intermediate | advanced
    created_at: float = field(default_factory=time.time)


@dataclass
class ConversationTurn:
    role: str
    content: str
    agent: str
    timestamp: float = field(default_factory=time.time)


class SessionManager:
    """Persists users, conversation history, and portfolios via SQLAlchemy.

    Connects to PostgreSQL (RDS) when DATABASE_URL is set; falls back to
    SQLite for local development.
    """

    def __init__(self, database_url: str = "sqlite:///data/sessions.db"):
        if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
            db_path = database_url[len("sqlite:///"):]
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        is_sqlite = database_url.startswith("sqlite")
        connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {}

        # For SQLite use NullPool to avoid connection sharing surprises in threaded contexts.
        poolclass = NullPool if is_sqlite else None

        engine_kwargs = dict(pool_pre_ping=True)
        if poolclass is not None:
            engine_kwargs["poolclass"] = poolclass

        self.engine = create_engine(
            database_url,
            connect_args=connect_args,
            **engine_kwargs,
        )

        # Prefer migrations when requested, otherwise fall back to metadata.create_all for dev
        use_migrations = os.environ.get("USE_ALEMBIC_MIGRATIONS", "false").lower() in ("1", "true", "yes")
        if use_migrations:
            try:
                # Run alembic upgrade head programmatically if available
                from alembic.config import Config
                from alembic import command

                cfg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'alembic.ini')
                cfg = Config(os.path.abspath(cfg_path))
                # Ensure sqlalchemy.url is set to current database
                cfg.set_main_option('sqlalchemy.url', database_url)
                command.upgrade(cfg, 'head')
                logger.info("Applied Alembic migrations (head)")
            except Exception as e:
                logger.warning(f"Failed to run Alembic migrations: {e}. Falling back to create_all.")
                try:
                    Base.metadata.create_all(self.engine)
                except Exception as e2:
                    logger.warning(f"Failed to create DB schema (continuing): {e2}")
        else:
            try:
                # Schema creation may race in concurrent startups; log and continue on failure
                Base.metadata.create_all(self.engine)
            except Exception as e:
                logger.warning(f"Failed to create DB schema (continuing): {e}")

        # Use scoped_session so sessions are thread-local and easier to manage in web servers
        self._Session = scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))
        self._cache: Dict[str, Dict] = {}

        display_url = database_url.split("@")[-1] if "@" in database_url else database_url
        logger.info(f"SessionManager connected to {display_url}")

    @contextmanager
    def session_scope(self, retries: int = 3, backoff: float = 0.1):
        """Provide a transactional scope around a series of operations.

        Retries a few times on transient OperationalError.
        """
        attempt = 0
        while True:
            attempt += 1
            db = self._Session()
            try:
                yield db
                db.commit()
                break
            except OperationalError as oe:
                db.rollback()
                logger.warning(f"OperationalError on DB access (attempt {attempt}): {oe}")
                if attempt >= retries:
                    raise
                time.sleep(backoff * attempt)
            except Exception:
                db.rollback()
                raise
            finally:
                try:
                    db.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    ALLOWED_RISK_TOLERANCE = {"conservative", "moderate", "aggressive"}

    def _resolve_user_id(self, session_id: str, user_id: Optional[str] = None) -> str:
        with self.session_scope() as db:
            session_record = db.get(SessionRecord, session_id)

            if user_id:
                user = db.get(UserRecord, user_id)
                if user is None:
                    user = UserRecord(user_id=user_id)
                    db.add(user)

                if session_record:
                    if session_record.user_id != user_id:
                        session_record.user_id = user_id
                else:
                    db.add(SessionRecord(session_id=session_id, user_id=user_id))
                return user_id

            if session_record:
                return session_record.user_id

            user = db.get(UserRecord, session_id)
            if user is None:
                user = UserRecord(user_id=session_id)
                db.add(user)

            db.add(SessionRecord(session_id=session_id, user_id=session_id))
            return session_id

    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> Dict:
        if session_id in self._cache:
            return self._cache[session_id]

        canonical_user_id = self._resolve_user_id(session_id, user_id=user_id)

        with self.session_scope() as db:
            user = db.get(UserRecord, canonical_user_id)
            if user is None:
                user = UserRecord(user_id=canonical_user_id)
                db.add(user)

            profile = UserProfile(
                user_id=user.user_id,
                risk_tolerance=user.risk_tolerance,
                investment_horizon=user.investment_horizon,
                experience_level=user.experience_level,
                created_at=user.created_at,
            )

            rows = (
                db.query(HistoryRecord)
                .filter(HistoryRecord.user_id == canonical_user_id)
                .order_by(HistoryRecord.id.desc())
                .limit(100)
                .all()
            )
            history = [
                ConversationTurn(role=r.role, content=r.content, agent=r.agent, timestamp=r.timestamp)
                for r in reversed(rows)
            ]

            rec = db.get(PortfolioRecord, canonical_user_id)
            portfolio = json.loads(rec.portfolio_json) if rec else None

        self._cache[session_id] = {"profile": profile, "history": history, "portfolio": portfolio}
        return self._cache[session_id]

    def add_message(self, session_id: str, role: str, content: str, agent: str = "system", user_id: Optional[str] = None):
        session = self.get_or_create_session(session_id, user_id=user_id)
        turn = ConversationTurn(role=role, content=content, agent=agent)
        session["history"].append(turn)
        canonical_user_id = self._resolve_user_id(session_id, user_id=user_id)
        with self.session_scope() as db:
            db.add(HistoryRecord(
                user_id=canonical_user_id, role=role, content=content,
                agent=agent, timestamp=turn.timestamp,
            ))

    def get_history(self, session_id: str, last_n: int = 10) -> List[Dict]:
        session = self.get_or_create_session(session_id)
        turns = session["history"][-last_n:]
        return [{"role": t.role, "content": t.content} for t in turns]

    def update_portfolio(self, session_id: str, portfolio: Dict, user_id: Optional[str] = None):
        session = self.get_or_create_session(session_id, user_id=user_id)
        session["portfolio"] = portfolio
        payload = json.dumps(portfolio)
        canonical_user_id = self._resolve_user_id(session_id, user_id=user_id)
        with self.session_scope() as db:
            rec = db.get(PortfolioRecord, canonical_user_id)
            if rec:
                rec.portfolio_json = payload
                rec.updated_at = time.time()
            else:
                db.add(PortfolioRecord(user_id=canonical_user_id, portfolio_json=payload))

    def get_portfolio(self, session_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        return self.get_or_create_session(session_id, user_id=user_id).get("portfolio")

    def update_profile(self, session_id: str, **kwargs):
        if "risk_tolerance" in kwargs:
            risk_value = kwargs["risk_tolerance"]
            if risk_value not in self.ALLOWED_RISK_TOLERANCE:
                raise ValueError(
                    "risk_tolerance must be one of: conservative, moderate, aggressive"
                )

        session = self.get_or_create_session(session_id)
        for k, v in kwargs.items():
            if hasattr(session["profile"], k):
                setattr(session["profile"], k, v)
        canonical_user_id = self._resolve_user_id(session_id)
        with self.session_scope() as db:
            user = db.get(UserRecord, canonical_user_id)
            if user:
                for k, v in kwargs.items():
                    if hasattr(user, k):
                        setattr(user, k, v)
                user.updated_at = time.time()

    def get_profile(self, session_id: str, user_id: Optional[str] = None) -> UserProfile:
        return self.get_or_create_session(session_id, user_id=user_id)["profile"]

    def link_session_to_user(self, session_id: str, user_id: str) -> None:
        if not session_id or not user_id:
            return
        canonical_user_id = self._resolve_user_id(session_id, user_id=user_id)
        self._cache.pop(session_id, None)
        self._resolve_user_id(session_id, user_id=canonical_user_id)

    # ------------------------------------------------------------------ #
    # User management                                                      #
    # ------------------------------------------------------------------ #

    def list_users(self) -> List[UserProfile]:
        with self.session_scope() as db:
            return [
                UserProfile(
                    user_id=u.user_id,
                    risk_tolerance=u.risk_tolerance,
                    investment_horizon=u.investment_horizon,
                    experience_level=u.experience_level,
                    created_at=u.created_at,
                )
                for u in db.query(UserRecord).all()
            ]

    def delete_user(self, session_id: str):
        self._cache.pop(session_id, None)
        with self.session_scope() as db:
            db.query(HistoryRecord).filter(HistoryRecord.user_id == session_id).delete()
            db.query(PortfolioRecord).filter(PortfolioRecord.user_id == session_id).delete()
            db.query(UserRecord).filter(UserRecord.user_id == session_id).delete()
