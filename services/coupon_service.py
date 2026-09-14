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

def create_coupon(code: str, coupon_type: str, value: int, max_uses: int = -1, expires_at: datetime.datetime = None):
    session = SessionLocal()
    try:
        coupon = Coupon(
            id=str(uuid.uuid4()),
            code=code.upper(),
            type=coupon_type,
            value=value,
            max_uses=max_uses,
            used_count=0,
            active=True,
            expires_at=expires_at
        )
        session.add(coupon)
        session.commit()
        log_action("COUPON_CREATED", f"Cupom {code} ({coupon_type} - {value}) criado")
        return coupon
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

        # Apply Bonus Coins
        if coupon.type == "COIN_BONUS":
            user.coins += coupon.value
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
                coins=coupon.value,
                amount_brl=0.0,
                description=f"Resgate do Cupom '{coupon.code}'"
            )
            session.add(tx)
            session.commit()

            log_action("COUPON_REDEEMED", f"Usuário {user.username} resgatou cupom {coupon.code} (+{coupon.value} Coins)", target_id=user.id)
            return True, f"Cupom resgatado com sucesso! +{coupon.value} Coins adicionadas ao seu saldo."

        return False, "Tipo de cupom não suportado para resgate direto."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao aplicar cupom: {str(e)}"
    finally:
        session.close()
