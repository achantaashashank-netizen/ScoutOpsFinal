"""
Simplified migration script that adds RAG columns WITHOUT pgvector.
This uses PostgreSQL arrays for embeddings instead of the vector type.

Usage:
    python -m scripts.add_rag_columns_simple
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from sqlalchemy import text


def run_migration():
    """
    Add RAG columns without requiring pgvector extension.
    Uses PostgreSQL ARRAY type for embeddings instead.
    """
    db = SessionLocal()

    try:
        print("Starting simplified RAG migration (without pgvector)...")

        # Step 1: Add embedding column as ARRAY type (works without extension)
        print("1. Adding embedding column (as REAL[] array)...")
        try:
            db.execute(text("""
                ALTER TABLE notes
                ADD COLUMN IF NOT EXISTS embedding REAL[];
            """))
            db.commit()
            print("   [OK] embedding column added")
        except Exception as e:
            print(f"   Note: embedding column may already exist - {e}")
            db.rollback()

        # Step 2: Add text_searchable column
        print("2. Adding text_searchable column...")
        try:
            db.execute(text("""
                ALTER TABLE notes
                ADD COLUMN IF NOT EXISTS text_searchable tsvector;
            """))
            db.commit()
            print("   [OK] text_searchable column added")
        except Exception as e:
            print(f"   Note: text_searchable column may already exist - {e}")
            db.rollback()

        # Step 3: Create GIN index for text_searchable
        print("3. Creating GIN index for text search...")
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_note_text_search
                ON notes USING GIN (text_searchable);
            """))
            db.commit()
            print("   [OK] GIN index created")
        except Exception as e:
            print(f"   Note: Index may already exist - {e}")
            db.rollback()

        print("\n[SUCCESS] Migration completed successfully!")
        print("\nNote: Using REAL[] for embeddings (pgvector not required)")
        print("Semantic search will use array operations instead of vector ops")
        print("\nNext steps:")
        print("1. Run: python -m scripts.backfill_embeddings")
        print("2. This will generate embeddings for all existing notes")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
