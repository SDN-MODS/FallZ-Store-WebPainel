import uuid
import xml.etree.ElementTree as ET
from database.db import SessionLocal
from database.models import DayzTypeItem
from services.audit_service import log_action

def process_types_xml_content(xml_content: str):
    """Parses DayZ types.xml content and saves unique item names into DayzTypeItem."""
    session = SessionLocal()
    try:
        root = ET.fromstring(xml_content)
        count = 0

        # DayZ types.xml structure: <types><type name="ItemClassName"><category name="weapons"/></type></types>
        for type_elem in root.findall('type'):
            name = type_elem.get('name')
            if not name:
                continue

            category_elem = type_elem.find('category')
            category_name = category_elem.get('name') if category_elem is not None else None

            existing = session.query(DayzTypeItem).filter_by(name=name).first()
            if not existing:
                item = DayzTypeItem(
                    id=str(uuid.uuid4()),
                    name=name,
                    category=category_name
                )
                session.add(item)
                count += 1

        session.commit()
        log_action("TYPES_XML_UPLOADED", f"Arquivo types.xml processado. {count} novos itens cadastrados para autocomplete.")
        return True, f"{count} novos itens de itens do DayZ importados com sucesso!"
    except Exception as e:
        session.rollback()
        return False, f"Erro ao processar arquivo types.xml: {str(e)}"
    finally:
        session.close()

def get_all_type_item_names():
    session = SessionLocal()
    try:
        items = session.query(DayzTypeItem.name).order_by(DayzTypeItem.name.asc()).all()
        return [i[0] for i in items]
    finally:
        session.close()
