import uuid
from sqlalchemy import func
from database.db import SessionLocal
from database.models import Ticket, TicketMessage, User
from services.audit_service import log_action

def create_ticket(user_id: str, category: str, subject: str, initial_message: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return False, "Usuário não encontrado.", None

        max_num = session.query(func.max(Ticket.ticket_num)).scalar() or 100
        next_num = max_num + 1

        ticket = Ticket(
            id=str(uuid.uuid4()),
            ticket_num=next_num,
            user_id=user.id,
            category=category,
            subject=subject,
            status="Aberto"
        )
        session.add(ticket)
        session.flush()

        msg = TicketMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            sender_id=user.id,
            sender_name=user.username,
            is_admin=False,
            content=initial_message
        )
        session.add(msg)
        session.commit()

        log_action("TICKET_CREATED", f"Ticket #{ticket.ticket_num} aberto por {user.username} (Categoria: {category})", target_id=user.id)
        return True, f"Ticket #{ticket.ticket_num} aberto com sucesso!", ticket.id
    except Exception as e:
        session.rollback()
        return False, f"Erro ao criar ticket: {str(e)}", None
    finally:
        session.close()

def get_user_tickets(user_id: str):
    session = SessionLocal()
    try:
        return session.query(Ticket).filter_by(user_id=user_id).order_by(Ticket.created_at.desc()).all()
    finally:
        session.close()

def get_all_tickets():
    session = SessionLocal()
    try:
        return session.query(Ticket).order_by(Ticket.created_at.desc()).all()
    finally:
        session.close()

def get_ticket_by_id(ticket_id: str):
    session = SessionLocal()
    try:
        return session.query(Ticket).filter_by(id=ticket_id).first()
    finally:
        session.close()

def add_ticket_message(ticket_id: str, sender_id: str, sender_name: str, is_admin: bool, content: str):
    session = SessionLocal()
    try:
        ticket = session.query(Ticket).filter_by(id=ticket_id).first()
        if not ticket:
            return False, "Ticket não encontrado."

        msg = TicketMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            sender_id=sender_id,
            sender_name=sender_name,
            is_admin=is_admin,
            content=content
        )
        session.add(msg)
        ticket.status = "Em Atendimento" if is_admin else ticket.status
        session.commit()
        return True, "Mensagem enviada com sucesso."
    except Exception as e:
        session.rollback()
        return False, f"Erro ao responder ticket: {str(e)}"
    finally:
        session.close()

def close_ticket(ticket_id: str):
    session = SessionLocal()
    try:
        ticket = session.query(Ticket).filter_by(id=ticket_id).first()
        if ticket:
            ticket.status = "Fechado"
            session.commit()
            log_action("TICKET_CLOSED", f"Ticket #{ticket.ticket_num} foi fechado.")
            return True, "Ticket fechado com sucesso."
        return False, "Ticket não encontrado."
    finally:
        session.close()
