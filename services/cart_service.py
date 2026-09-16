import uuid
from database.db import SessionLocal
from database.models import CartItem, Product, User
from services.user_service import get_or_create_user
from services.order_service import create_order

def get_db():
    return SessionLocal()

def add_to_cart(user_id: str, product_id: str, quantity: int = 1, username: str = "Player"):
    """Adiciona um produto ao carrinho do usuário ou incrementa a quantidade se já existir."""
    session = get_db()
    try:
        get_or_create_user(user_id, username=username)

        product = session.query(Product).filter_by(id=product_id, active=True).first()
        if not product:
            return False, "Produto não encontrado ou inativo."

        cart_item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                id=str(uuid.uuid4()),
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            session.add(cart_item)

        session.commit()
        return True, f"**{product.name}** adicionado ao carrinho com sucesso!"
    except Exception as e:
        session.rollback()
        return False, f"Erro ao adicionar produto ao carrinho: {str(e)}"
    finally:
        session.close()

def get_cart_items(user_id: str):
    """Retorna os itens do carrinho do usuário com detalhes do produto e o total de Coins."""
    session = get_db()
    try:
        items = session.query(CartItem).filter_by(user_id=user_id).all()
        cart_data = []
        total_coins = 0

        for item in items:
            product = session.query(Product).filter_by(id=item.product_id).first()
            if product:
                subtotal = product.price_coins * item.quantity
                total_coins += subtotal
                cart_data.append({
                    "cart_item_id": item.id,
                    "product_id": product.id,
                    "name": product.name,
                    "price_coins": product.price_coins,
                    "quantity": item.quantity,
                    "subtotal_coins": subtotal
                })

        user = session.query(User).filter_by(id=user_id).first()
        user_coins = user.coins if user else 0

        return {
            "items": cart_data,
            "total_coins": total_coins,
            "user_coins": user_coins
        }
    finally:
        session.close()

def remove_from_cart(user_id: str, product_id: str):
    """Remove um item específico do carrinho."""
    session = get_db()
    try:
        cart_item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            session.delete(cart_item)
            session.commit()
            return True, "Item removido do carrinho."
        return False, "Item não encontrado no carrinho."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def clear_cart(user_id: str):
    """Esvazia o carrinho do usuário."""
    session = get_db()
    try:
        session.query(CartItem).filter_by(user_id=user_id).delete()
        session.commit()
        return True, "Carrinho esvaziado."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()

def checkout_cart(user_id: str):
    """
    Processa a compra de todos os itens do carrinho.
    Deduz Coins do usuário e gera um Pedido.
    """
    session = get_db()
    try:
        cart_items = session.query(CartItem).filter_by(user_id=user_id).all()
        if not cart_items:
            return False, "Seu carrinho está vazio."

        items_payload = [{'product_id': ci.product_id, 'quantity': ci.quantity} for ci in cart_items]
        session.close() # Fechar antes de delegar para create_order

        ok, msg, order_id = create_order(user_id, items_payload)
        if ok:
            clear_cart(user_id)
            return True, f"🎉 Compra do carrinho realizada com sucesso!"
        else:
            return False, msg

    except Exception as e:
        return False, f"Erro ao finalizar compra: {str(e)}"
