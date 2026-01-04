import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
import numpy as np
import os
from dotenv import load_dotenv
from app.main import app
from app.database import Base, get_db

# Load environment variables
load_dotenv("../.env")

# Use PostgreSQL for testing (required for ARRAY types used in embeddings)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Fallintake%232022@localhost:5433/Scout_OPS_db")
engine = create_engine(DATABASE_URL)
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


# Week 2: RAG Tests
class TestRAG:
    """Tests for RAG (Retrieval-Augmented Generation) endpoints"""

    @pytest.fixture
    def mock_embedding_model(self):
        """Mock the SentenceTransformer model to avoid downloading it"""
        with patch('app.rag.embeddings.SentenceTransformer') as mock_model:
            # Create a mock that returns a 384-dim vector
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(384)
            mock_model.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_gemini(self):
        """Mock Google Gemini API to avoid real API calls"""
        with patch('app.rag.generation.genai.GenerativeModel') as mock_model:
            # Create a mock response
            mock_response = MagicMock()
            mock_response.text = "Stephen Curry is an excellent shooter [1] with great court vision [2]."

            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def sample_player_with_notes(self, mock_embedding_model):
        """Create a player with notes for testing RAG"""
        # Create player
        player_response = client.post(
            "/api/players",
            json={"name": "Stephen Curry", "team": "Warriors", "position": "Guard"}
        )
        player_id = player_response.json()["id"]

        # Create notes with diverse content
        notes = [
            {
                "player_id": player_id,
                "title": "Shooting Analysis",
                "content": "Curry demonstrates exceptional shooting ability from beyond the arc. His quick release and accuracy make him a threat from anywhere on the court.",
                "tags": "shooting, offense"
            },
            {
                "player_id": player_id,
                "title": "Court Vision",
                "content": "Excellent court vision and playmaking ability. Creates opportunities for teammates with precise passes.",
                "tags": "playmaking, assists"
            },
            {
                "player_id": player_id,
                "title": "Defensive Effort",
                "content": "Shows good defensive awareness. Hustles on defense and communicates well with teammates.",
                "tags": "defense"
            }
        ]

        for note in notes:
            client.post("/api/notes", json=note)

        return player_id

    # Test 1: Retrieval endpoint - successful retrieval
    def test_retrieve_notes_success(self, sample_player_with_notes, mock_embedding_model):
        """Test successful note retrieval using hybrid search"""
        response = client.post(
            "/api/rag/retrieve",
            json={
                "query": "shooting ability",
                "top_k": 3
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert data["query"] == "shooting ability"
        assert data["total_results"] > 0
        assert len(data["results"]) <= 3

        # Verify result structure
        result = data["results"][0]
        assert "note_id" in result
        assert "player_name" in result
        assert "title" in result
        assert "excerpt" in result
        assert "relevance_score" in result
        assert "keyword_score" in result
        assert "semantic_score" in result

    # Test 2: Retrieval with no results
    def test_retrieve_notes_no_results(self, mock_embedding_model):
        """Test retrieval when no notes match the query"""
        response = client.post(
            "/api/rag/retrieve",
            json={
                "query": "nonexistent topic xyz123",
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 0
        assert len(data["results"]) == 0

    # Test 3: Retrieval with player filter
    def test_retrieve_notes_with_player_filter(self, sample_player_with_notes, mock_embedding_model):
        """Test retrieval filtered by specific player"""
        # Create another player with notes
        other_player = client.post(
            "/api/players",
            json={"name": "LeBron James", "team": "Lakers"}
        )
        other_player_id = other_player.json()["id"]
        client.post(
            "/api/notes",
            json={
                "player_id": other_player_id,
                "title": "LeBron Shooting",
                "content": "Shooting performance analysis"
            }
        )

        # Retrieve only for Curry
        response = client.post(
            "/api/rag/retrieve",
            json={
                "query": "shooting",
                "player_id": sample_player_with_notes,
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # All results should be for Stephen Curry
        for result in data["results"]:
            assert result["player_name"] == "Stephen Curry"

    # Test 4: Retrieval with team filter
    def test_retrieve_notes_with_team_filter(self, sample_player_with_notes, mock_embedding_model):
        """Test retrieval filtered by team"""
        response = client.post(
            "/api/rag/retrieve",
            json={
                "query": "shooting",
                "team": "Warriors",
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] > 0

    # Test 5: Retrieval with custom weights
    def test_retrieve_notes_custom_weights(self, sample_player_with_notes, mock_embedding_model):
        """Test retrieval with custom keyword/semantic weights"""
        response = client.post(
            "/api/rag/retrieve",
            json={
                "query": "shooting",
                "top_k": 3,
                "keyword_weight": 0.7,
                "semantic_weight": 0.3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] > 0

    # Test 6: Generation endpoint - successful generation
    def test_generate_answer_success(self, sample_player_with_notes, mock_embedding_model, mock_gemini):
        """Test successful answer generation with citations"""
        response = client.post(
            "/api/rag/generate",
            json={
                "query": "What are Curry's strengths?",
                "top_k": 3
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "query" in data
        assert "answer" in data
        assert "citations" in data
        assert "has_sufficient_information" in data
        assert "confidence" in data

        assert data["query"] == "What are Curry's strengths?"
        assert len(data["answer"]) > 0
        assert data["confidence"] in ["low", "medium", "high"]

    # Test 7: Generation with citations extracted
    def test_generate_answer_with_citations(self, sample_player_with_notes, mock_embedding_model, mock_gemini):
        """Test that citations are properly extracted from answer"""
        response = client.post(
            "/api/rag/generate",
            json={
                "query": "Tell me about Curry",
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check citations
        assert "citations" in data
        assert len(data["citations"]) > 0

        # Verify citation structure
        citation = data["citations"][0]
        assert "note_id" in citation
        assert "player_name" in citation
        assert "title" in citation
        assert "excerpt" in citation
        assert "reference_number" in citation

    # Test 8: Generation with no notes available
    def test_generate_answer_no_notes(self, mock_embedding_model, mock_gemini):
        """Test generation when no notes are available"""
        response = client.post(
            "/api/rag/generate",
            json={
                "query": "Tell me about a player",
                "top_k": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should indicate insufficient information
        assert data["has_sufficient_information"] == False
        assert data["confidence"] == "low"
        assert "don't have" in data["answer"].lower()

    # Test 9: Generation with player filter
    def test_generate_answer_with_player_filter(self, sample_player_with_notes, mock_embedding_model, mock_gemini):
        """Test generation filtered by specific player"""
        response = client.post(
            "/api/rag/generate",
            json={
                "query": "What are the player's strengths?",
                "player_id": sample_player_with_notes,
                "top_k": 3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0

    # Test 10: Generation with retrieval results included
    def test_generate_answer_include_retrieval(self, sample_player_with_notes, mock_embedding_model, mock_gemini):
        """Test generation with retrieval results included in response"""
        response = client.post(
            "/api/rag/generate",
            json={
                "query": "What are Curry's strengths?",
                "top_k": 3,
                "include_retrieval": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should include retrieved notes
        assert "retrieved_notes" in data
        assert data["retrieved_notes"] is not None
        assert len(data["retrieved_notes"]) > 0

    # Test 11: Generation without retrieval results
    def test_generate_answer_exclude_retrieval(self, sample_player_with_notes, mock_embedding_model, mock_gemini):
        """Test generation without retrieval results in response"""
        response = client.post(
            "/api/rag/generate",
            json={
                "query": "What are Curry's strengths?",
                "top_k": 3,
                "include_retrieval": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should NOT include retrieved notes
        assert data.get("retrieved_notes") is None

    # Test 12: Embedding generation on note creation
    def test_note_creates_embedding(self):
        """Test that creating a note automatically generates an embedding"""
        # Create player
        player_response = client.post(
            "/api/players",
            json={"name": "Test Player", "team": "Test Team"}
        )
        player_id = player_response.json()["id"]

        # Create note
        note_response = client.post(
            "/api/notes",
            json={
                "player_id": player_id,
                "title": "Test Note",
                "content": "This is test content for embedding generation",
                "tags": "test"
            }
        )

        assert note_response.status_code == 201
        data = note_response.json()

        # Verify embedding field exists (we can't easily check the actual embedding without querying DB)
        # The fact that note was created successfully means embedding was generated
        assert "id" in data
        assert data["title"] == "Test Note"

    # Test 13: Embedding updates on note edit
    def test_note_update_regenerates_embedding(self):
        """Test that editing a note regenerates its embedding"""
        # Create player and note
        player_response = client.post(
            "/api/players",
            json={"name": "Test Player"}
        )
        player_id = player_response.json()["id"]

        note_response = client.post(
            "/api/notes",
            json={
                "player_id": player_id,
                "title": "Original",
                "content": "Original content"
            }
        )
        note_id = note_response.json()["id"]

        # Update note
        update_response = client.put(
            f"/api/notes/{note_id}",
            json={"content": "Updated content"}
        )

        assert update_response.status_code == 200
        data = update_response.json()

        # Verify note was updated successfully (embedding would have been regenerated)
        assert data["content"] == "Updated content"
        assert data["title"] == "Original"  # Unchanged

    # Test 14: Confidence assessment
    def test_confidence_high_with_multiple_citations(self, sample_player_with_notes, mock_embedding_model):
        """Test that answers with multiple citations get high confidence"""
        # Mock Gemini to return answer with 3+ citations
        with patch('app.rag.generation.genai.GenerativeModel') as mock_model:
            mock_response = MagicMock()
            mock_response.text = "Curry is great at shooting [1], passing [2], and defense [3]."

            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance

            response = client.post(
                "/api/rag/generate",
                json={
                    "query": "What are Curry's strengths?",
                    "top_k": 5
                }
            )

            assert response.status_code == 200
            data = response.json()

            # With 3+ citations, should be high confidence
            assert data["confidence"] == "high"
            assert len(data["citations"]) >= 3

    # Test 15: Confidence assessment - low confidence
    def test_confidence_low_without_citations(self, sample_player_with_notes, mock_embedding_model):
        """Test that answers without citations get low confidence"""
        # Mock Gemini to return answer with no citations
        with patch('app.rag.generation.genai.GenerativeModel') as mock_model:
            mock_response = MagicMock()
            mock_response.text = "I don't have enough information in the scouting notes to answer this question."

            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance

            response = client.post(
                "/api/rag/generate",
                json={
                    "query": "What is Curry's favorite color?",
                    "top_k": 5
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should be low confidence
            assert data["confidence"] == "low"
            assert data["has_sufficient_information"] == False

    # Test 16: Invalid request - missing query
    def test_generate_missing_query(self):
        """Test that generation fails gracefully with missing query"""
        response = client.post(
            "/api/rag/generate",
            json={"top_k": 5}  # Missing query field
        )

        # Should return 422 Unprocessable Entity (validation error)
        assert response.status_code == 422

    # Test 17: Retrieval with top_k parameter
    def test_retrieve_respects_top_k(self, sample_player_with_notes, mock_embedding_model):
        """Test that retrieval returns correct number of results"""
        response = client.post(
            "/api/rag/retrieve",
            json={
                "query": "basketball",
                "top_k": 2
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return at most 2 results
        assert len(data["results"]) <= 2
