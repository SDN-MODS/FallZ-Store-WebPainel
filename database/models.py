import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True) # Discord ID
    username = Column(String, nullable=False)
    discriminator = Column(String, default="0")
    avatar = Column(String, nullable=True)
    coins = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    coin_transactions = relationship("CoinTransaction", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan")
    coupon_usages = relationship("CouponUsage", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class CoinPackage(Base):
    __tablename__ = 'coin_packages'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    coins = Column(Integer, nullable=False)
    bonus_coins = Column(Integer, default=0)
    price_brl = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CoinTransaction(Base):
    __tablename__ = 'coin_transactions'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String, nullable=False) # PURCHASE, SPENT, ADMIN_ADD, ADMIN_REMOVE, BONUS, REFUND
    coins = Column(Integer, nullable=False)
    amount_brl = Column(Float, default=0.0)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="coin_transactions")


class Category(Base):
    __tablename__ = 'categories'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = 'products'

    id = Column(String, primary_key=True)
    category_id = Column(String, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price_coins = Column(Integer, nullable=False)
    stock = Column(Integer, default=-1) # -1 = infinito
    image_url = Column(String, nullable=True)
    display_order = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = 'orders'

    id = Column(String, primary_key=True)
    order_number = Column(Integer, autoincrement=True, unique=True, nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    total_coins = Column(Integer, nullable=False)
    status = Column(String, default="Aguardando processamento") # "Aguardando processamento", "Processando", "Entregue", "Cancelado"
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(String, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_coins = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Coupon(Base):
    __tablename__ = 'coupons'

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False) # COIN_BONUS, COIN_DISCOUNT
    value = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=-1)
    used_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(Base):
    __tablename__ = 'coupon_usages'

    id = Column(String, primary_key=True)
    coupon_id = Column(String, ForeignKey('coupons.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User", back_populates="coupon_usages")


class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(String, primary_key=True)
    ticket_num = Column(Integer, autoincrement=True, unique=True, nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category = Column(String, nullable=False) # Coins, Pagamento, Pedido, Entrega, Outros
    subject = Column(String, nullable=True)
    status = Column(String, default="Aberto") # Aberto, Em Atendimento, Fechado
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(Base):
    __tablename__ = 'ticket_messages'

    id = Column(String, primary_key=True)
    ticket_id = Column(String, ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(String, primary_key=True)
    actor_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=False)
    target_id = Column(String, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class StoreSettings(Base):
    __tablename__ = 'store_settings'

    id = Column(String, primary_key=True, default="default")
    store_name = Column(String, default="FallZ Store DayZ")
    logo_url = Column(String, default="https://i.imgur.com/8Q9Z5Xm.png")
    support_channel_id = Column(String, default="")
    orders_channel_id = Column(String, default="")
    admin_role_id = Column(String, default="")
    bot_welcome_message = Column(Text, default="Bem-vindo à Loja DayZ! Compre Coins e resgate seus itens com facilidade.")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
