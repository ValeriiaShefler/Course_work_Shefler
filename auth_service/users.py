#CRUD операции с пользователями с использованием SQLAlchemy
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import User
from auth import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, username: str, password: str, avatar: str = None):
    password_hash = hash_password(password)
    user = User(
        email=email,
        username=username,
        password_hash=password_hash,
        avatar=avatar
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_email(db: AsyncSession, user_id: int, email: str):
    await db.execute(
        update(User).where(User.id == user_id).values(email=email)
    )
    await db.commit()


async def update_user_username(db: AsyncSession, user_id: int, username: str):
    await db.execute(
        update(User).where(User.id == user_id).values(username=username)
    )
    await db.commit()


async def update_user_password(db: AsyncSession, user_id: int, new_password: str):
    new_hash = hash_password(new_password)
    await db.execute(
        update(User).where(User.id == user_id).values(password_hash=new_hash)
    )
    await db.commit()


async def delete_user(db: AsyncSession, user_id: int):
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


async def check_email_exists(db: AsyncSession, email: str, exclude_user_id: int = None):
    query = select(User.id).where(User.email == email)
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def check_username_exists(db: AsyncSession, username: str, exclude_user_id: int = None):
    query = select(User.id).where(User.username == username)
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()