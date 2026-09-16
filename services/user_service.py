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
            if user.username != username or user.avatar != avatar:
                user.username = username
                user.avatar = avatar
                session.commit()
                session.refresh(user)
        return user
    finally:
        session.close()

def is_user_registered(discord_id: str) -> bool:
    """Verifica se o usuário já completou seu cadastro (Nome, Nick e Steam ID)."""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=discord_id).first()
        if user and user.full_name and user.nick and user.steam_id:
            return True
        return False
    finally:
        session.close()

def register_user(discord_id: str, username: str, full_name: str, nick: str, steam_id: str, discriminator: str = "0", avatar: str = None):
    """Realiza ou atualiza o cadastro completo de um jogador."""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=discord_id).first()
        if not user:
            user = User(
                id=discord_id,
                username=username,
                discriminator=discriminator,
                avatar=avatar,
                full_name=full_name.strip(),
                nick=nick.strip(),
                steam_id=steam_id.strip(),
                coins=0
            )
            session.add(user)
        else:
            user.username = username
            user.full_name = full_name.strip()
            user.nick = nick.strip()
            user.steam_id = steam_id.strip()
            if avatar:
                user.avatar = avatar

        session.commit()
        session.refresh(user)
        return True, f"🎉 Cadastro realizado com sucesso, **{nick}**! Agora você tem acesso completo à loja."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao realizar cadastro: {str(e)}"
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
