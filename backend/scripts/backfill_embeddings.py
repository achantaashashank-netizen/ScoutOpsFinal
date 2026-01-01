"""
Backfill script to generate embeddings and text_searchable for existing notes.
Run this after adding the RAG columns to populate them with data.

Usage:
    python -m scripts.backfill_embeddings
"""
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Note
from app.rag.embeddings import generate_embedding, generate_text_searchable
from sqlalchemy import func


def backfill_embeddings():
    """
    Generate embeddings and text_searchable for all notes that don't have them.
    """
    db = SessionLocal()

    try:
        # Find notes without embeddings
        notes_without_embeddings = db.query(Note).filter(Note.embedding.is_(None)).all()

        total_notes = len(notes_without_embeddings)

        if total_notes == 0:
            print("✓ All notes already have embeddings!")
            return

        print(f"Found {total_notes} notes without embeddings. Starting backfill...")
        print("-" * 60)

        for i, note in enumerate(notes_without_embeddings, 1):
            try:
                # Generate combined text for embedding
                combined_text = f"{note.title} {note.content}"
                if note.tags:
                    combined_text += f" {note.tags}"

                # Generate embedding
                note.embedding = generate_embedding(combined_text)

                # Generate text_searchable
                note.text_searchable = func.to_tsvector(
                    'english',
                    generate_text_searchable(note.title, note.content, note.tags or "")
                )

                db.commit()

                print(f"[{i}/{total_notes}] ✓ Indexed note {note.id}: '{note.title[:50]}'")

            except Exception as e:
                print(f"[{i}/{total_notes}] ✗ Failed to index note {note.id}: {e}")
                db.rollback()
                continue

        print("-" * 60)
        print(f"✓ Backfill completed! Indexed {total_notes} notes.")

    except Exception as e:
        print(f"✗ Backfill failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_embeddings()
