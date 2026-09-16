import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base, StoreSettings, BotEmbedTemplate

DB_FILE = os.getenv("DATABASE_URL", "sqlite:///dayz_store.db")

engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))

def seed_default_embed_templates(session):
    defaults = [
        BotEmbedTemplate(
            key="main_menu",
            name="Menu Principal da Loja",
            title="🏪 LOJA DAYZ — MENU PRINCIPAL",
            description="Seja bem-vindo à nossa loja virtual!\nUse os botões abaixo para navegar sem precisar digitar comandos.",
            color="#FFD700",
            footer_text="Regra Central: Dinheiro ➔ Coins ➔ Produtos"
        ),
        BotEmbedTemplate(
            key="coin_store",
            name="Loja de Coins",
            title="🪙 ADQUIRIR COINS — MOEDA VIRTUAL",
            description="Escolha um dos pacotes abaixo para recarregar seu saldo de Coins instantaneamente!",
            color="#FFD700",
            footer_text="Ao selecionar um pacote, o pagamento é processado e as coins entram no seu saldo."
        ),
        BotEmbedTemplate(
            key="category_list",
            name="Lista de Categorias",
            title="🛒 LOJA — CATEGORIAS DISPONÍVEIS",
            description="Selecione a categoria desejada no menu suspenso abaixo para ver os itens.",
            color="#3B82F6",
            footer_text="Navegação por botões e menus interativos."
        ),
        BotEmbedTemplate(
            key="product_detail",
            name="Detalhes do Produto / Kit",
            title="📦 DETALHES DO PRODUTO / KIT",
            description="Confira as informações, itens inclusos e saldo necessário para efetuar o resgate.",
            color="#8B5CF6",
            footer_text="Resgate instantâneo com saldo de Coins."
        ),
        BotEmbedTemplate(
            key="balance_info",
            name="Meu Saldo & Extrato",
            title="💰 SEU SALDO & HISTÓRICO DE COINS",
            description="Consulte abaixo seu saldo em Coins e suas últimas movimentações.",
            color="#10B981",
            footer_text="Sistema de Economia DayZ Store."
        ),
        BotEmbedTemplate(
            key="order_list",
            name="Meus Pedidos",
            title="📦 MEUS PEDIDOS & STATUS",
            description="Confira abaixo o histórico de seus pedidos e o status de entrega no servidor.",
            color="#F59E0B",
            footer_text="Acompanhamento em tempo real."
        ),
        BotEmbedTemplate(
            key="ticket_support",
            name="Central de Suporte",
            title="🎫 CENTRAL DE SUPORTE TÉCNICO",
            description="Selecione abaixo a categoria que melhor se adapta à sua solicitação para abrir um ticket.",
            color="#EF4444",
            footer_text="Atendimento rápido com a equipe de administração."
        ),
        BotEmbedTemplate(
            key="shopping_cart",
            name="Carrinho de Compras",
            title="🛒 SEU CARRINHO DE COMPRAS",
            description="Confira os itens selecionados e o total em Coins antes de finalizar sua compra.",
            color="#F59E0B",
            footer_text="Finalize seu pedido ou continue navegando na loja!"
        ),
        BotEmbedTemplate(
            key="coupon_broadcast",
            name="Divulgação de Cupons no Canal",
            title="🎁 CUPOM PROMOCIONAL DISPONÍVEL!",
            description="Um novo cupom promocional está ativo no servidor! Clique no botão abaixo para resgatar instantaneamente no seu saldo.",
            color="#10B981",
            footer_text="Aproveite antes que os resgates se esgotem!"
        ),
        BotEmbedTemplate(
            key="registration_prompt",
            name="Confirmação de Cadastro do Jogador",
            title="📝 CADASTRO DE JOGADOR REGISTRADO",
            description="Seus dados foram vinculados com sucesso ao servidor. Agora você tem acesso completo a todas as funções da loja virtual!",
            color="#3B82F6",
            footer_text="Aproveite as compras e bom jogo!"
        ),
        BotEmbedTemplate(
            key="purchase_success",
            name="Confirmação de Compra Realizada",
            title="🎉 COMPRA REALIZADA COM SUCESSO!",
            description="Seu pedido foi registrado na loja e está aguardando o processamento da nossa equipe.",
            color="#10B981",
            footer_text="Acompanhe o status do seu pedido em 'Meus Pedidos'."
        )
    ]

    for t in defaults:
        existing = session.query(BotEmbedTemplate).filter_by(key=t.key).first()
        if not existing:
            session.add(t)
    session.commit()

def migrate_db():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(store_settings)")).fetchall()
        columns = [row[1] for row in result]
        if 'bot_client_id' not in columns:
            conn.execute(text("ALTER TABLE store_settings ADD COLUMN bot_client_id VARCHAR DEFAULT ''"))
        if 'bot_token' not in columns:
            conn.execute(text("ALTER TABLE store_settings ADD COLUMN bot_token VARCHAR DEFAULT ''"))
        if 'bot_invite_url' not in columns:
            conn.execute(text("ALTER TABLE store_settings ADD COLUMN bot_invite_url VARCHAR DEFAULT ''"))
        if 'store_channel_id' not in columns:
            conn.execute(text("ALTER TABLE store_settings ADD COLUMN store_channel_id VARCHAR DEFAULT ''"))

        pkg_result = conn.execute(text("PRAGMA table_info(coin_packages)")).fetchall()
        pkg_columns = [row[1] for row in pkg_result]
        if 'image_url' not in pkg_columns:
            conn.execute(text("ALTER TABLE coin_packages ADD COLUMN image_url VARCHAR"))

        user_result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        user_columns = [row[1] for row in user_result]
        if 'full_name' not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
        if 'nick' not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN nick VARCHAR"))
        if 'steam_id' not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN steam_id VARCHAR"))

        coupon_result = conn.execute(text("PRAGMA table_info(coupons)")).fetchall()
        coupon_columns = [row[1] for row in coupon_result]
        if 'channel_id' not in coupon_columns:
            conn.execute(text("ALTER TABLE coupons ADD COLUMN channel_id VARCHAR"))
        if 'interval_minutes' not in coupon_columns:
            conn.execute(text("ALTER TABLE coupons ADD COLUMN interval_minutes INTEGER DEFAULT 0"))
        if 'start_time' not in coupon_columns:
            conn.execute(text("ALTER TABLE coupons ADD COLUMN start_time DATETIME"))
        if 'last_sent_at' not in coupon_columns:
            conn.execute(text("ALTER TABLE coupons ADD COLUMN last_sent_at DATETIME"))

        conn.commit()

def init_db():
    Base.metadata.create_all(bind=engine)
    try:
        migrate_db()
    except Exception as e:
        print(f"Migração de esquema: {e}")

    session = SessionLocal()
    try:
        settings = session.query(StoreSettings).filter_by(id="default").first()
        if not settings:
            settings = StoreSettings(id="default")
            session.add(settings)
            session.commit()

        seed_default_embed_templates(session)
    finally:
        session.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
