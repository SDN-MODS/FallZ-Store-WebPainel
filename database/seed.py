import uuid
from database.db import init_db, SessionLocal
from database.models import CoinPackage, Category, Product, Coupon, StoreSettings

def seed():
    init_db()
    session = SessionLocal()
    try:
        # Seed Coin Packages if empty
        if session.query(CoinPackage).count() == 0:
            packages = [
                CoinPackage(id=str(uuid.uuid4()), title="100 Coins", coins=100, bonus_coins=0, price_brl=10.0, description="Pacote básico de Coins"),
                CoinPackage(id=str(uuid.uuid4()), title="250 Coins", coins=250, bonus_coins=10, price_brl=25.0, description="Pacote recomendado com +10 Coins bônus"),
                CoinPackage(id=str(uuid.uuid4()), title="500 Coins", coins=500, bonus_coins=30, price_brl=50.0, description="Pacote avançado com +30 Coins bônus"),
                CoinPackage(id=str(uuid.uuid4()), title="1.000 Coins", coins=1000, bonus_coins=100, price_brl=95.0, description="Pacote popular com +100 Coins bônus"),
                CoinPackage(id=str(uuid.uuid4()), title="2.500 Coins", coins=2500, bonus_coins=300, price_brl=220.0, description="Pacote VIP com +300 Coins bônus"),
            ]
            session.add_all(packages)
            print("✓ Pacotes de Coins semeados!")

        # Seed Categories if empty
        if session.query(Category).count() == 0:
            cat_armas = Category(id=str(uuid.uuid4()), name="Armas", description="Armamentos para combate em Chernarus/Livonia", display_order=1)
            cat_equip = Category(id=str(uuid.uuid4()), name="Equipamentos", description="Mochilas, coletes e acessórios táticos", display_order=2)
            cat_veic = Category(id=str(uuid.uuid4()), name="Veículos", description="Carros e helicópteros prontos para andar", display_order=3)

            session.add_all([cat_armas, cat_equip, cat_veic])
            session.commit()

            # Seed Products
            products = [
                Product(id=str(uuid.uuid4()), category_id=cat_armas.id, name="AK-74", description="Fuzil de assalto soviético 5.45x39mm com carregador extra.", price_coins=350, stock=50, image_url="https://i.imgur.com/AK74_placeholder.png", display_order=1),
                Product(id=str(uuid.uuid4()), category_id=cat_armas.id, name="M4A1", description="Fuzil de assalto ocidental 5.56x45mm de alta precisão.", price_coins=500, stock=30, image_url="https://i.imgur.com/M4A1_placeholder.png", display_order=2),
                Product(id=str(uuid.uuid4()), category_id=cat_equip.id, name="Colete Balístico", description="Colete pesado de proteção nível 4.", price_coins=250, stock=100, image_url="https://i.imgur.com/Vest_placeholder.png", display_order=1),
                Product(id=str(uuid.uuid4()), category_id=cat_equip.id, name="Mochila Campo 90L", description="Mochila tática militar de alta capacidade.", price_coins=150, stock=-1, image_url="https://i.imgur.com/Backpack_placeholder.png", display_order=2),
                Product(id=str(uuid.uuid4()), category_id=cat_veic.id, name="Veículo Ada 4x4", description="Carro off-road de 4 lugares completo com gasolina e vela.", price_coins=1500, stock=10, image_url="https://i.imgur.com/Car_placeholder.png", display_order=1),
            ]
            session.add_all(products)
            print("✓ Categorias e Produtos semeados!")

        # Seed Coupons if empty
        if session.query(Coupon).count() == 0:
            coupons = [
                Coupon(id=str(uuid.uuid4()), code="BENVINDO", type="COIN_BONUS", value=50, max_uses=100, active=True),
                Coupon(id=str(uuid.uuid4()), code="DAYZ2025", type="COIN_BONUS", value=100, max_uses=50, active=True)
            ]
            session.add_all(coupons)
            print("✓ Cupons de teste semeados!")

        session.commit()
        print("✓ Banco de dados semeado com sucesso!")
    except Exception as e:
        session.rollback()
        print(f"Erro ao semear banco: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed()
