"""
Database migration script: Remove embedding column from PostgreSQL.
This should be run after Qdrant is set up and embeddings are migrated.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine


def migrate_database():
    """
    Remove the embedding column from the notes table.
    Embeddings are now stored in Qdrant instead of PostgreSQL.
    """
    print("=" * 60)
    print("Migrating Database Schema")
    print("=" * 60)

    with engine.connect() as connection:
        # Check if embedding column exists
        print("\n[1/2] Checking if embedding column exists...")
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='notes' AND column_name='embedding'
        """))

        column_exists = result.fetchone() is not None

        if column_exists:
            print("  ✓ Found embedding column - will remove it")

            print("\n[2/2] Dropping embedding column from notes table...")
            try:
                connection.execute(text("ALTER TABLE notes DROP COLUMN IF EXISTS embedding"))
                connection.commit()
                print("  ✓ Successfully removed embedding column")
                print("\n  Note: Embeddings are now stored in Qdrant vector database")
            except Exception as e:
                print(f"  ✗ Failed to drop column: {e}")
                return False
        else:
            print("  ✓ Embedding column already removed - nothing to do")

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
