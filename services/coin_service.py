import uuid
from database.db import SessionLocal
from database.models import CoinPackage, CoinTransaction, User
from services.audit_service import log_action

def get_active_coin_packages():
    session = SessionLocal()
    try:
        return session.query(CoinPackage).filter_by(active=True).all()
    finally:
        session.close()

def get_coin_package_by_id(package_id: str):
    session = SessionLocal()
    try:
        return session.query(CoinPackage).filter_by(id=package_id).first()
    finally:
        session.close()

def create_coin_package(title: str, coins: int, bonus_coins: int, price_brl: float, description: str = ""):
    session = SessionLocal()
    try:
        pkg = CoinPackage(
            id=str(uuid.uuid4()),
            title=title,
            coins=coins,
            bonus_coins=bonus_coins,
            price_brl=price_brl,
            description=description,
            active=True
        )
        session.add(pkg)
        session.commit()
        session.refresh(pkg)
        log_action("PACKAGE_CREATED", f"Pacote {title} ({coins} Coins) criado por R$ {price_brl:.2f}")
        return pkg
    finally:
        session.close()

def update_coin_package(package_id: str, title: str, coins: int, bonus_coins: int, price_brl: float, active: bool):
    session = SessionLocal()
    try:
        pkg = session.query(CoinPackage).filter_by(id=package_id).first()
        if pkg:
            pkg.title = title
            pkg.coins = coins
            pkg.bonus_coins = bonus_coins
            pkg.price_brl = price_brl
            pkg.active = active
            session.commit()
            log_action("PACKAGE_UPDATED", f"Pacote {title} atualizado")
            return pkg
        return None
    finally:
        session.close()

def process_coin_purchase(user_id: str, package_id: str):
    session = SessionLocal()
    try:
        pkg = session.query(CoinPackage).filter_by(id=package_id).first()
        user = session.query(User).filter_by(id=user_id).first()

        if not pkg or not user:
            return False, "Pacote ou usuário não encontrado."

        total_coins = pkg.coins + pkg.bonus_coins
        user.coins += total_coins

        transaction = CoinTransaction(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type="PURCHASE",
            coins=total_coins,
            amount_brl=pkg.price_brl,
            description=f"Compra do pacote '{pkg.title}' ({pkg.coins} + {pkg.bonus_coins} bônus)"
        )

        session.add(transaction)
        session.commit()

        log_action(
            "COIN_PURCHASE",
            f"Usuário {user.username} ({user.id}) comprou pacote {pkg.title} por R${pkg.price_brl:.2f} e recebeu {total_coins} Coins",
            target_id=user.id
        )
        return True, f"Pagamento Aprovado! {total_coins} Coins adicionadas ao seu saldo."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao processar compra: {str(e)}"
    finally:
        session.close()

def adjust_user_coins_manually(admin_id: str, user_id: str, amount: int, reason: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False, "Usuário não encontrado."

        tx_type = "ADMIN_ADD" if amount >= 0 else "ADMIN_REMOVE"
        user.coins += amount
        if user.coins < 0:
            user.coins = 0

        transaction = CoinTransaction(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type=tx_type,
            coins=amount,
            amount_brl=0.0,
            description=f"Ajuste manual de Administrador: {reason}"
        )

        session.add(transaction)
        session.commit()

        log_action(
            "ADMIN_COIN_ADJUSTMENT",
            f"Admin {admin_id} alterou saldo de {user.username} em {amount} Coins. Motivo: {reason}",
            actor_id=admin_id,
            target_id=user.id
        )
        return True, f"Saldo atualizado com sucesso. Saldo atual: {user.coins} Coins."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao ajustar saldo: {str(e)}"
    finally:
        session.close()

def get_user_coin_transactions(user_id: str):
    session = SessionLocal()
    try:
        return session.query(CoinTransaction).filter_by(user_id=user_id).order_by(CoinTransaction.created_at.desc()).all()
    finally:
        session.close()
