from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from app import models, schemas
from app.rag.embeddings import generate_text_searchable, store_note_embedding
from app.rag.vector_store import delete_note_embedding


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
        # Get all note IDs for this player (to delete from Qdrant)
        note_ids = [note.id for note in db_player.notes]

        # Delete player from PostgreSQL (cascades to notes)
        db.delete(db_player)
        db.commit()

        # Delete associated note embeddings from Qdrant
        for note_id in note_ids:
            try:
                delete_note_embedding(note_id)
            except Exception as e:
                print(f"Warning: Failed to delete embedding from Qdrant for note {note_id}: {e}")

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

    # Week 2: Generate text_searchable for keyword search (PostgreSQL)
    db_note.text_searchable = func.to_tsvector(
        'english',
        generate_text_searchable(note.title, note.content, note.tags or "")
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # Store embedding in Qdrant vector database
    try:
        store_note_embedding(db_note, db)
    except Exception as e:
        print(f"Warning: Failed to store embedding in Qdrant for note {db_note.id}: {e}")

    return db_note


def update_note(db: Session, note_id: int, note: schemas.NoteUpdate):
    db_note = get_note(db, note_id)
    if db_note:
        update_data = note.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_note, key, value)

        # Week 2: Regenerate text_searchable and embeddings if content changed
        if any(k in update_data for k in ['title', 'content', 'tags']):
            # Update PostgreSQL full-text search
            db_note.text_searchable = func.to_tsvector(
                'english',
                generate_text_searchable(db_note.title, db_note.content, db_note.tags or "")
            )

        db.commit()
        db.refresh(db_note)

        # Update embedding in Qdrant if content changed
        if any(k in update_data for k in ['title', 'content', 'tags']):
            try:
                store_note_embedding(db_note, db)
            except Exception as e:
                print(f"Warning: Failed to update embedding in Qdrant for note {db_note.id}: {e}")

    return db_note


def delete_note(db: Session, note_id: int):
    db_note = get_note(db, note_id)
    if db_note:
        # Delete from PostgreSQL
        db.delete(db_note)
        db.commit()

        # Delete from Qdrant vector database
        try:
            delete_note_embedding(note_id)
        except Exception as e:
            print(f"Warning: Failed to delete embedding from Qdrant for note {note_id}: {e}")

        return True
    return False
