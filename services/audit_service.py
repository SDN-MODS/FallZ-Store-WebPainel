import uuid
from database.db import SessionLocal
from database.models import AuditLog

def log_action(action: str, details: str, actor_id: str = None, target_id: str = None):
    session = SessionLocal()
    try:
        log = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=actor_id,
            action=action,
            details=details,
            target_id=target_id
        )
        session.add(log)
        session.commit()
        return log
    except Exception as e:
        session.rollback()
        print(f"Erro ao salvar audit log: {e}")
    finally:
        session.close()

def get_audit_logs(limit: int = 100):
    session = SessionLocal()
    try:
        return session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    finally:
        session.close()
