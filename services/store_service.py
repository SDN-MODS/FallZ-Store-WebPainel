import uuid
from sqlalchemy.orm import joinedload
from database.db import SessionLocal
from database.models import Category, Product, ProductContentItem
from services.audit_service import log_action

def get_active_categories():
    session = SessionLocal()
    try:
        return session.query(Category).filter_by(active=True).order_by(Category.display_order.asc()).all()
    finally:
        session.close()

def get_all_categories():
    session = SessionLocal()
    try:
        return session.query(Category).order_by(Category.display_order.asc()).all()
    finally:
        session.close()

def create_category(name: str, description: str = "", display_order: int = 0):
    session = SessionLocal()
    try:
        cat = Category(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            display_order=display_order,
            active=True
        )
        session.add(cat)
        session.commit()
        session.refresh(cat)
        log_action("CATEGORY_CREATED", f"Categoria {name} criada")
        return cat
    finally:
        session.close()

def get_products_by_category(category_id: str, only_active: bool = True):
    session = SessionLocal()
    try:
        query = session.query(Product).options(joinedload(Product.content_items)).filter_by(category_id=category_id)
        if only_active:
            query = query.filter_by(active=True)
        return query.order_by(Product.display_order.asc()).all()
    finally:
        session.close()

def get_product_by_id(product_id: str):
    session = SessionLocal()
    try:
        return session.query(Product).options(joinedload(Product.content_items)).filter_by(id=product_id).first()
    finally:
        session.close()

def create_product(category_id: str, name: str, description: str, price_coins: int, stock: int = -1, image_url: str = "", content_items: list = None):
    """
    content_items format:
    [{'item_name': str, 'quantity': int, 'is_single_use': bool, 'expiration_days': int}]
    """
    session = SessionLocal()
    try:
        prod = Product(
            id=str(uuid.uuid4()),
            category_id=category_id,
            name=name,
            description=description,
            price_coins=price_coins,
            stock=stock,
            image_url=image_url,
            active=True
        )
        session.add(prod)
        session.flush()

        if content_items:
            for item in content_items:
                if item.get('item_name'):
                    c_item = ProductContentItem(
                        id=str(uuid.uuid4()),
                        product_id=prod.id,
                        item_name=item['item_name'],
                        quantity=item.get('quantity', 1),
                        is_single_use=item.get('is_single_use', True),
                        expiration_days=item.get('expiration_days', 0)
                    )
                    session.add(c_item)

        session.commit()
        session.refresh(prod)
        log_action("PRODUCT_CREATED", f"Produto '{name}' ({price_coins} Coins) com {len(content_items or [])} itens internos criado")
        return prod
    finally:
        session.close()

def update_product(product_id: str, name: str, description: str, price_coins: int, stock: int, image_url: str, active: bool, category_id: str, content_items: list = None):
    session = SessionLocal()
    try:
        prod = session.query(Product).filter_by(id=product_id).first()
        if prod:
            prod.name = name
            prod.description = description
            prod.price_coins = price_coins
            prod.stock = stock
            prod.image_url = image_url
            prod.active = active
            prod.category_id = category_id

            # Clear old content items and replace
            session.query(ProductContentItem).filter_by(product_id=prod.id).delete()

            if content_items:
                for item in content_items:
                    if item.get('item_name'):
                        c_item = ProductContentItem(
                            id=str(uuid.uuid4()),
                            product_id=prod.id,
                            item_name=item['item_name'],
                            quantity=item.get('quantity', 1),
                            is_single_use=item.get('is_single_use', True),
                            expiration_days=item.get('expiration_days', 0)
                        )
                        session.add(c_item)

            session.commit()
            log_action("PRODUCT_UPDATED", f"Produto '{name}' atualizado")
            return prod
        return None
    finally:
        session.close()

def delete_product(product_id: str):
    session = SessionLocal()
    try:
        prod = session.query(Product).filter_by(id=product_id).first()
        if prod:
            name = prod.name
            session.delete(prod)
            session.commit()
            log_action("PRODUCT_DELETED", f"Produto '{name}' excluído")
            return True
        return False
    finally:
        session.close()
