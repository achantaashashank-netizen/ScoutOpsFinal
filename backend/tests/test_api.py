import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestPlayers:
    def test_create_player(self):
        response = client.post(
            "/api/players",
            json={
                "name": "Test Player",
                "position": "Guard",
                "team": "Test Team",
                "jersey_number": 23
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Player"
        assert data["position"] == "Guard"
        assert "id" in data

    def test_list_players(self):
        # Create a player first
        client.post(
            "/api/players",
            json={"name": "Player 1", "team": "Team A"}
        )

        response = client.get("/api/players")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Player 1"

    def test_get_player(self):
        # Create a player
        create_response = client.post(
            "/api/players",
            json={"name": "Test Player", "team": "Test Team"}
        )
        player_id = create_response.json()["id"]

        # Get the player
        response = client.get(f"/api/players/{player_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Player"

    def test_get_nonexistent_player(self):
        response = client.get("/api/players/9999")
        assert response.status_code == 404

    def test_update_player(self):
        # Create a player
        create_response = client.post(
            "/api/players",
            json={"name": "Original Name", "team": "Team A"}
        )
        player_id = create_response.json()["id"]

        # Update the player
        response = client.put(
            f"/api/players/{player_id}",
            json={"name": "Updated Name", "team": "Team B"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["team"] == "Team B"

    def test_delete_player(self):
        # Create a player
        create_response = client.post(
            "/api/players",
            json={"name": "To Delete", "team": "Team"}
        )
        player_id = create_response.json()["id"]

        # Delete the player
        response = client.delete(f"/api/players/{player_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/players/{player_id}")
        assert get_response.status_code == 404

    def test_search_players(self):
        # Create multiple players
        client.post("/api/players", json={"name": "Stephen Curry", "team": "Warriors"})
        client.post("/api/players", json={"name": "LeBron James", "team": "Lakers"})

        # Search by name
        response = client.get("/api/players?search=Curry")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Stephen Curry"


class TestNotes:
    def test_create_note(self):
        # Create a player first
        player_response = client.post(
            "/api/players",
            json={"name": "Test Player", "team": "Test Team"}
        )
        player_id = player_response.json()["id"]

        # Create a note
        response = client.post(
            "/api/notes",
            json={
                "player_id": player_id,
                "title": "Test Note",
                "content": "This is a test note content",
                "tags": "test, demo"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Note"
        assert data["player_id"] == player_id

    def test_create_note_invalid_player(self):
        response = client.post(
            "/api/notes",
            json={
                "player_id": 9999,
                "title": "Test",
                "content": "Content"
            }
        )
        assert response.status_code == 404

    def test_list_notes_by_player(self):
        # Create a player
        player_response = client.post(
            "/api/players",
            json={"name": "Test Player"}
        )
        player_id = player_response.json()["id"]

        # Create notes
        client.post(
            "/api/notes",
            json={"player_id": player_id, "title": "Note 1", "content": "Content 1"}
        )
        client.post(
            "/api/notes",
            json={"player_id": player_id, "title": "Note 2", "content": "Content 2"}
        )

        # List notes for player
        response = client.get(f"/api/notes?player_id={player_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_note(self):
        # Create player and note
        player_response = client.post(
            "/api/players",
            json={"name": "Test Player"}
        )
        player_id = player_response.json()["id"]

        note_response = client.post(
            "/api/notes",
            json={"player_id": player_id, "title": "Original", "content": "Content"}
        )
        note_id = note_response.json()["id"]

        # Update note
        response = client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Content"  # Unchanged

    def test_delete_note(self):
        # Create player and note
        player_response = client.post(
            "/api/players",
            json={"name": "Test Player"}
        )
        player_id = player_response.json()["id"]

        note_response = client.post(
            "/api/notes",
            json={"player_id": player_id, "title": "To Delete", "content": "Content"}
        )
        note_id = note_response.json()["id"]

        # Delete note
        response = client.delete(f"/api/notes/{note_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 404
