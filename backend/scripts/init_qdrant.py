"""
Initialize Qdrant collection and migrate existing embeddings.
Run this script on startup to ensure Qdrant is ready.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app import models
from app.rag.vector_store import ensure_collection_exists, get_collection_info
from app.rag.embeddings import store_note_embedding


def init_qdrant():
    """
    Initialize Qdrant collection and migrate existing notes.
    """
    print("=" * 60)
    print("Initializing Qdrant Vector Database")
    print("=" * 60)

    # Step 1: Ensure collection exists
    print("\n[Step 1/3] Creating Qdrant collection if it doesn't exist...")
    try:
        ensure_collection_exists()
    except Exception as e:
        print(f"✗ Failed to create collection: {e}")
        return False

    # Step 2: Check collection status
    print("\n[Step 2/3] Checking collection status...")
    try:
        info = get_collection_info()
        if "error" in info:
            print(f"✗ Error getting collection info: {info['error']}")
            return False
        print(f"✓ Collection ready: {info['points_count']} vectors stored")
    except Exception as e:
        print(f"✗ Failed to get collection info: {e}")
        return False

    # Step 3: Migrate existing notes (only if collection is empty or has fewer notes than DB)
    print("\n[Step 3/3] Checking if migration is needed...")
    db = SessionLocal()
    try:
        # Count notes in PostgreSQL
        total_notes = db.query(models.Note).count()
        print(f"  - PostgreSQL has {total_notes} notes")
        print(f"  - Qdrant has {info['points_count']} vectors")

        if info['points_count'] < total_notes:
            print(f"\n  ⚠ Migration needed: {total_notes - info['points_count']} notes missing from Qdrant")
            print("  Starting migration...\n")

            # Get all notes with player relationships
            notes = db.query(models.Note).join(models.Player).all()

            migrated = 0
            failed = 0

            for i, note in enumerate(notes, 1):
                try:
                    # Store embedding in Qdrant
                    success = store_note_embedding(note, db)
                    if success:
                        migrated += 1
                        if i % 10 == 0:
                            print(f"  Progress: {i}/{total_notes} notes processed...")
                    else:
                        failed += 1
                except Exception as e:
                    print(f"  ✗ Failed to migrate note {note.id}: {e}")
                    failed += 1

            print(f"\n  ✓ Migration complete!")
            print(f"    - Successfully migrated: {migrated} notes")
            if failed > 0:
                print(f"    - Failed: {failed} notes")

        else:
            print("  ✓ No migration needed - Qdrant is up to date")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("Qdrant initialization complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = init_qdrant()
    sys.exit(0 if success else 1)
