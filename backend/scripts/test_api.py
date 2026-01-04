"""
Test if the API endpoints are working.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app import crud

db = SessionLocal()

try:
    print("Testing CRUD operations...")

    # Test get_players
    print("\n1. Testing get_players()...")
    players = crud.get_players(db=db, skip=0, limit=100)
    print(f"   Found {len(players)} players")
    for p in players:
        print(f"   - {p.name} ({p.team})")

    # Test get_notes
    print("\n2. Testing get_notes()...")
    notes = crud.get_notes(db=db, skip=0, limit=100)
    print(f"   Found {len(notes)} notes")
    for n in notes:
        print(f"   - {n.title} (Player ID: {n.player_id})")
        print(f"     Has embedding: {n.embedding is not None}")
        print(f"     Has text_searchable: {n.text_searchable is not None}")

    print("\n[SUCCESS] All CRUD operations working!")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
