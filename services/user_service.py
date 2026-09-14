from database.db import SessionLocal
from database.models import User

def get_or_create_user(discord_id: str, username: str, discriminator: str = "0", avatar: str = None):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=discord_id).first()
        if not user:
            user = User(
                id=discord_id,
                username=username,
                discriminator=discriminator,
                avatar=avatar,
                coins=0
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Update user info if changed
            if user.username != username or user.avatar != avatar:
                user.username = username
                user.avatar = avatar
                session.commit()
                session.refresh(user)
        return user
    finally:
        session.close()

def get_user_balance(discord_id: str) -> int:
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=discord_id).first()
        return user.coins if user else 0
    finally:
        session.close()

def get_all_users():
    session = SessionLocal()
    try:
        return session.query(User).all()
    finally:
        session.close()
