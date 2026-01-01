"""
Check database schema and tables.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from sqlalchemy import text, inspect

db = SessionLocal()

try:
    # Check if tables exist
    print("Checking database tables...")
    result = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """))
    tables = [row[0] for row in result]
    print(f"Tables: {tables}")

    # Check notes table structure
    if 'notes' in tables:
        print("\nNotes table columns:")
        result = db.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'notes'
            ORDER BY ordinal_position
        """))
        for row in result:
            print(f"  - {row[0]}: {row[1]}")

    # Count players and notes
    if 'players' in tables:
        result = db.execute(text("SELECT COUNT(*) FROM players"))
        player_count = result.scalar()
        print(f"\nPlayers in database: {player_count}")

    if 'notes' in tables:
        result = db.execute(text("SELECT COUNT(*) FROM notes"))
        note_count = result.scalar()
        print(f"Notes in database: {note_count}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
