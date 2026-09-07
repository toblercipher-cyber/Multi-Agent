"""
crud.py
-------
Database read/write helpers. Each function does exactly one thing —
call these from your FastAPI routes, don't write raw queries in routes.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import User, UserQuery, LLMResponse


async def get_or_create_user(db: AsyncSession, email: str) -> User:
    """Finds the user by email, or creates them if this is their first time.
    Always increments login_count and updates last_login."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, login_count=1, last_login=func.now())
        db.add(user)
    else:
        user.login_count += 1
        user.last_login = func.now()

    await db.commit()
    await db.refresh(user)
    return user


async def create_query(db: AsyncSession, user_id: int, query_text: str) -> UserQuery:
    """Logs a new user query, returns the row (with its generated query_id)."""
    query = UserQuery(user_id=user_id, query_text=query_text)
    db.add(query)
    await db.commit()
    await db.refresh(query)
    return query


async def create_response(db: AsyncSession, query_id: int, response_text: str) -> LLMResponse:
    """Logs the final LLM response tied to a specific query."""
    response = LLMResponse(query_id=query_id, response_text=response_text)
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response