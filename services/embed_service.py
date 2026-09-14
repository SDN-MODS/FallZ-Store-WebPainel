from database.db import SessionLocal
from database.models import BotEmbedTemplate
from services.audit_service import log_action

def get_all_embed_templates():
    session = SessionLocal()
    try:
        return session.query(BotEmbedTemplate).all()
    finally:
        session.close()

def get_embed_template(key: str):
    session = SessionLocal()
    try:
        tpl = session.query(BotEmbedTemplate).filter_by(key=key).first()
        if not tpl:
            # Fallback default
            tpl = BotEmbedTemplate(
                key=key,
                name=key.replace('_', ' ').title(),
                title=f"PROPRIEDADE DE {key.upper()}",
                description="Descrição padrão",
                color="#FFD700"
            )
        return tpl
    finally:
        session.close()

def update_embed_template(key: str, title: str, description: str, color: str, footer_text: str = "", thumbnail_url: str = "", image_url: str = ""):
    session = SessionLocal()
    try:
        tpl = session.query(BotEmbedTemplate).filter_by(key=key).first()
        if not tpl:
            tpl = BotEmbedTemplate(key=key, name=key.replace('_', ' ').title())
            session.add(tpl)

        tpl.title = title
        tpl.description = description
        tpl.color = color if color.startswith('#') else f"#{color}"
        tpl.footer_text = footer_text
        tpl.thumbnail_url = thumbnail_url
        tpl.image_url = image_url

        session.commit()
        log_action("EMBED_TEMPLATE_UPDATED", f"Embed '{key}' customizado via painel web.")
        return True, "Embed atualizado com sucesso!"
    except Exception as e:
        session.rollback()
        return False, f"Erro ao atualizar embed: {str(e)}"
    finally:
        session.close()
