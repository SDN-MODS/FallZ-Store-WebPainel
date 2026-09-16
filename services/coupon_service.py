import uuid
import datetime
from database.db import SessionLocal
from database.models import Coupon, CouponUsage, User, CoinTransaction
from services.audit_service import log_action

def get_all_coupons():
    session = SessionLocal()
    try:
        return session.query(Coupon).all()
    finally:
        session.close()

def create_coupon(code: str, coupon_type: str, value: int, applies_to: str = "ALL", target_id: str = None, max_uses: int = -1, channel_id: str = None, interval_minutes: int = 0, start_time: datetime.datetime = None, expires_at: datetime.datetime = None):
    session = SessionLocal()
    try:
        coupon = Coupon(
            id=str(uuid.uuid4()),
            code=code.upper(),
            type=coupon_type,
            value=value,
            applies_to=applies_to,
            target_id=target_id,
            max_uses=max_uses,
            used_count=0,
            active=True,
            channel_id=channel_id,
            interval_minutes=interval_minutes,
            start_time=start_time,
            expires_at=expires_at
        )
        session.add(coupon)
        session.commit()
        log_action("COUPON_CREATED", f"Cupom {code} ({coupon_type} - {value}, Escopo: {applies_to}) criado")
        return coupon
    finally:
        session.close()

def delete_coupon(coupon_id: str):
    session = SessionLocal()
    try:
        coupon = session.query(Coupon).filter_by(id=coupon_id).first()
        if coupon:
            code = coupon.code
            session.delete(coupon)
            session.commit()
            log_action("COUPON_DELETED", f"Cupom '{code}' ({coupon_id}) excluído.")
            return True, f"Cupom '{code}' excluído com sucesso."
        return False, "Cupom não encontrado."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao excluir cupom: {str(e)}"
    finally:
        session.close()

def toggle_coupon(coupon_id: str):
    session = SessionLocal()
    try:
        coupon = session.query(Coupon).filter_by(id=coupon_id).first()
        if coupon:
            coupon.active = not coupon.active
            session.commit()
            log_action("COUPON_TOGGLED", f"Status do cupom '{coupon.code}' alterado para {'Ativo' if coupon.active else 'Inativo'}.")
            return True, f"Status do cupom '{coupon.code}' atualizado."
        return False, "Cupom não encontrado."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def apply_coupon(user_id: str, code: str):
    session = SessionLocal()
    try:
        coupon = session.query(Coupon).filter_by(code=code.upper(), active=True).first()
        user = session.query(User).filter_by(id=user_id).first()

        if not coupon or not user:
            return False, "Cupom inválido ou não encontrado."

        if coupon.expires_at and coupon.expires_at < datetime.datetime.utcnow():
            return False, "Este cupom já expirou."

        if coupon.max_uses != -1 and coupon.used_count >= coupon.max_uses:
            return False, "Limite de uso deste cupom foi atingido."

        usage = session.query(CouponUsage).filter_by(coupon_id=coupon.id, user_id=user.id).first()
        if usage:
            return False, "Você já utilizou este cupom anteriormente."

        # Calcular bônus de Coins dependendo do tipo do cupom
        added_coins = 0
        if coupon.type == "COIN_BONUS":
            added_coins = coupon.value
        elif coupon.type == "COIN_BONUS_PERCENT":
            # Bônus percentual (ex: 20% de bônus em cima de 100 coins base = 20 coins)
            base_reference = 100
            added_coins = int(base_reference * (coupon.value / 100.0))
            if added_coins < 1:
                added_coins = coupon.value
        elif coupon.type == "DISCOUNT_FIXED":
            added_coins = coupon.value
        elif coupon.type == "DISCOUNT_PERCENT":
            base_reference = 100
            added_coins = int(base_reference * (coupon.value / 100.0))
            if added_coins < 1:
                added_coins = coupon.value
        else:
            added_coins = coupon.value

        user.coins += added_coins
        coupon.used_count += 1

        new_usage = CouponUsage(
            id=str(uuid.uuid4()),
            coupon_id=coupon.id,
            user_id=user.id
        )
        session.add(new_usage)

        tx = CoinTransaction(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type="BONUS",
            coins=added_coins,
            amount_brl=0.0,
            description=f"Resgate do Cupom '{coupon.code}' ({coupon.type})"
        )
        session.add(tx)
        session.commit()

        log_action("COUPON_REDEEMED", f"Usuário {user.username} resgatou cupom {coupon.code} (+{added_coins} Coins)", target_id=user.id)
        return True, f"🎉 Cupom **{coupon.code}** resgatado com sucesso! **+{added_coins} Coins** adicionadas ao seu saldo."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao aplicar cupom: {str(e)}"
    finally:
        session.close()
