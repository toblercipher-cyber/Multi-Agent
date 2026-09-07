"""
models.py
---------
SQLAlchemy ORM models — mirrors Multi-Agent.sql exactly (3 tables only).
"""

from sqlalchemy import BigInteger, String, Integer, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    last_login: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    queries: Mapped[list["UserQuery"]] = relationship(back_populates="user")


class UserQuery(Base):
    __tablename__ = "user_queries"

    query_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="queries")
    responses: Mapped[list["LLMResponse"]] = relationship(back_populates="query")


class LLMResponse(Base):
    __tablename__ = "llm_responses"

    response_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    query_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_queries.query_id", ondelete="CASCADE"), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    query: Mapped["UserQuery"] = relationship(back_populates="responses")