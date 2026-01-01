from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from app import models, schemas
from app.rag.embeddings import generate_embedding, generate_text_searchable


# Player CRUD operations
def get_player(db: Session, player_id: int):
    return db.query(models.Player).filter(models.Player.id == player_id).first()


def get_players(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    team: Optional[str] = None,
    position: Optional[str] = None
):
    query = db.query(models.Player)

    if search:
        search_filter = or_(
            models.Player.name.ilike(f"%{search}%"),
            models.Player.team.ilike(f"%{search}%"),
            models.Player.position.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if team:
        query = query.filter(models.Player.team.ilike(f"%{team}%"))

    if position:
        query = query.filter(models.Player.position.ilike(f"%{position}%"))

    return query.offset(skip).limit(limit).all()


def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = models.Player(**player.model_dump())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


def update_player(db: Session, player_id: int, player: schemas.PlayerUpdate):
    db_player = get_player(db, player_id)
    if db_player:
        update_data = player.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_player, key, value)
        db.commit()
        db.refresh(db_player)
    return db_player


def delete_player(db: Session, player_id: int):
    db_player = get_player(db, player_id)
    if db_player:
        db.delete(db_player)
        db.commit()
        return True
    return False


# Note CRUD operations
def get_note(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def get_notes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    player_id: Optional[int] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    is_important: Optional[bool] = None
):
    query = db.query(models.Note)

    if player_id:
        query = query.filter(models.Note.player_id == player_id)

    if search:
        search_filter = or_(
            models.Note.title.ilike(f"%{search}%"),
            models.Note.content.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if tag:
        query = query.filter(models.Note.tags.ilike(f"%{tag}%"))

    if is_important is not None:
        query = query.filter(models.Note.is_important == is_important)

    return query.order_by(models.Note.created_at.desc()).offset(skip).limit(limit).all()


def create_note(db: Session, note: schemas.NoteCreate):
    db_note = models.Note(**note.model_dump())

    # Week 2: Generate embeddings and text_searchable on creation
    combined_text = f"{note.title} {note.content}"
    if note.tags:
        combined_text += f" {note.tags}"

    db_note.embedding = generate_embedding(combined_text)
    db_note.text_searchable = func.to_tsvector(
        'english',
        generate_text_searchable(note.title, note.content, note.tags or "")
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def update_note(db: Session, note_id: int, note: schemas.NoteUpdate):
    db_note = get_note(db, note_id)
    if db_note:
        update_data = note.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_note, key, value)

        # Week 2: Regenerate embeddings if content changed
        if any(k in update_data for k in ['title', 'content', 'tags']):
            combined_text = f"{db_note.title} {db_note.content}"
            if db_note.tags:
                combined_text += f" {db_note.tags}"

            db_note.embedding = generate_embedding(combined_text)
            db_note.text_searchable = func.to_tsvector(
                'english',
                generate_text_searchable(db_note.title, db_note.content, db_note.tags or "")
            )

        db.commit()
        db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int):
    db_note = get_note(db, note_id)
    if db_note:
        db.delete(db_note)
        db.commit()
        return True
    return False
