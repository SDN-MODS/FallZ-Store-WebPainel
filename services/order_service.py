import uuid
from sqlalchemy import func
from database.db import SessionLocal
from database.models import Order, OrderItem, Product, User, CoinTransaction
from services.audit_service import log_action

def create_order(user_id: str, items: list):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False, "Usuário não encontrado.", None

        total_coins = 0
        order_items_data = []

        for item in items:
            product = session.query(Product).filter_by(id=item['product_id']).first()
            if not product or not product.active:
                return False, f"Produto indisponível.", None

            if product.stock != -1 and product.stock < item['quantity']:
                return False, f"Estoque insuficiente para {product.name}.", None

            item_total = product.price_coins * item['quantity']
            total_coins += item_total
            order_items_data.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_coins': product.price_coins
            })

        if user.coins < total_coins:
            return False, f"Saldo insuficiente. Você possui {user.coins} Coins e a compra exige {total_coins} Coins.", None

        # Calculate next order_number
        max_order_num = session.query(func.max(Order.order_number)).scalar() or 1000
        next_order_num = max_order_num + 1

        # Deduct coins from user balance
        user.coins -= total_coins

        # Create Order
        order = Order(
            id=str(uuid.uuid4()),
            order_number=next_order_num,
            user_id=user.id,
            total_coins=total_coins,
            status="Aguardando processamento"
        )
        session.add(order)
        session.flush()

        for data in order_items_data:
            if data['product'].stock != -1:
                data['product'].stock -= data['quantity']

            order_item = OrderItem(
                id=str(uuid.uuid4()),
                order_id=order.id,
                product_id=data['product'].id,
                quantity=data['quantity'],
                unit_coins=data['unit_coins']
            )
            session.add(order_item)

        # Record CoinTransaction
        transaction = CoinTransaction(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type="SPENT",
            coins=-total_coins,
            amount_brl=0.0,
            description=f"Compra do Pedido #{order.order_number}"
        )
        session.add(transaction)

        session.commit()

        log_action(
            "ORDER_CREATED",
            f"Pedido #{order.order_number} criado pelo usuário {user.username}. Total: {total_coins} Coins.",
            target_id=user.id
        )

        return True, "Pedido criado com sucesso!", order.id
    except Exception as e:
        session.rollback()
        return False, f"Erro ao criar pedido: {str(e)}", None
    finally:
        session.close()

def get_user_orders(user_id: str):
    session = SessionLocal()
    try:
        return session.query(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    finally:
        session.close()

def get_all_orders():
    session = SessionLocal()
    try:
        return session.query(Order).order_by(Order.created_at.desc()).all()
    finally:
        session.close()

def get_order_by_id(order_id: str):
    session = SessionLocal()
    try:
        return session.query(Order).filter_by(id=order_id).first()
    finally:
        session.close()

def update_order_status(order_id: str, status: str, admin_notes: str = "", refund: bool = False):
    session = SessionLocal()
    try:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            return False, "Pedido não encontrado."

        old_status = order.status
        order.status = status
        if admin_notes:
            order.admin_notes = admin_notes

        if refund and status == "Cancelado" and old_status != "Cancelado":
            user = session.query(User).filter_by(id=order.user_id).first()
            if user:
                user.coins += order.total_coins
                tx = CoinTransaction(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    type="REFUND",
                    coins=order.total_coins,
                    amount_brl=0.0,
                    description=f"Reembolso do Pedido #{order.order_number}"
                )
                session.add(tx)
                log_action("ORDER_REFUNDED", f"Reembolso de {order.total_coins} Coins para {user.username} do Pedido #{order.order_number}", target_id=user.id)

        session.commit()
        log_action("ORDER_STATUS_CHANGED", f"Status do Pedido #{order.order_number} alterado de '{old_status}' para '{status}'")
        return True, "Status do pedido atualizado com sucesso."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao atualizar pedido: {str(e)}"
    finally:
        session.close()
