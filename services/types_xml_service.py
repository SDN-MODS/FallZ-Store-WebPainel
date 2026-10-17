import uuid
import xml.etree.ElementTree as ET
from database.db import SessionLocal
from database.models import DayzTypeItem, DayzTypesFile
from services.audit_service import log_action

def process_types_xml_content(xml_content: str, filename: str, file_id: str = None):
    """Parses DayZ types.xml content and saves items linked to a DayzTypesFile."""
    session = SessionLocal()
    try:
        root = ET.fromstring(xml_content)
        count = 0

        if file_id:
            # Updating an existing file
            existing_file = session.query(DayzTypesFile).filter_by(id=file_id).first()
            if not existing_file:
                return False, "Arquivo types.xml selecionado não encontrado."
            # Clear old items
            session.query(DayzTypeItem).filter_by(file_id=file_id).delete()
            existing_file.filename = filename
            file_record = existing_file
        else:
            # New file upload
            file_id = str(uuid.uuid4())
            file_record = DayzTypesFile(id=file_id, filename=filename)
            session.add(file_record)

        # DayZ types.xml structure: <types><type name="ItemClassName"><category name="weapons"/></type></types>
        for type_elem in root.findall('type'):
            name = type_elem.get('name')
            if not name:
                continue

            category_elem = type_elem.find('category')
            category_name = category_elem.get('name') if category_elem is not None else None

            # Add new item for this file
            item = DayzTypeItem(
                id=str(uuid.uuid4()),
                file_id=file_record.id,
                name=name,
                category=category_name
            )
            session.add(item)
            count += 1

        session.commit()
        if file_id:
            log_action("TYPES_XML_UPDATED", f"Arquivo {filename} atualizado. {count} itens processados.")
        else:
            log_action("TYPES_XML_UPLOADED", f"Arquivo {filename} processado. {count} itens cadastrados.")

        return True, f"{count} itens de {filename} importados com sucesso!"
    except Exception as e:
        session.rollback()
        return False, f"Erro ao processar arquivo types.xml: {str(e)}"
    finally:
        session.close()

def delete_types_file(file_id: str):
    session = SessionLocal()
    try:
        file_record = session.query(DayzTypesFile).filter_by(id=file_id).first()
        if not file_record:
            return False, "Arquivo não encontrado."

        filename = file_record.filename
        session.delete(file_record)
        session.commit()
        log_action("TYPES_XML_DELETED", f"Arquivo {filename} excluído.")
        return True, f"Arquivo {filename} e seus itens foram removidos."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao excluir arquivo: {str(e)}"
    finally:
        session.close()

def get_all_types_files():
    session = SessionLocal()
    try:
        files = session.query(DayzTypesFile).order_by(DayzTypesFile.uploaded_at.desc()).all()
        return files
    finally:
        session.close()

def get_all_type_item_names():
    session = SessionLocal()
    try:
        # Use distinct to avoid duplicate names if multiple files have the same items
        items = session.query(DayzTypeItem.name).distinct().order_by(DayzTypeItem.name.asc()).all()
        return [i[0] for i in items]
    finally:
        session.close()
