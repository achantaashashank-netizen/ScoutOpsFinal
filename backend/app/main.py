from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
from app import models, schemas, crud
from app.database import engine, get_db

# Week 2: RAG imports
from app.rag import generation
from app.rag.schemas import (
    RetrievalRequest,
    RetrievalResponse,
    GenerationRequest,
    GenerationResponse
)
from app.rag.retrieval import retrieve_notes

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ScoutOps API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to ScoutOps API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Player endpoints
@app.post("/api/players", response_model=schemas.PlayerResponse, status_code=201)
async def create_player(
    player: schemas.PlayerCreate,
    db: Session = Depends(get_db)
):
    return crud.create_player(db=db, player=player)


@app.get("/api/players", response_model=List[schemas.PlayerResponse])
async def list_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    players = crud.get_players(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        team=team,
        position=position
    )
    return players


@app.get("/api/players/{player_id}", response_model=schemas.PlayerDetailResponse)
async def get_player(
    player_id: int,
    db: Session = Depends(get_db)
):
    player = crud.get_player(db=db, player_id=player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@app.put("/api/players/{player_id}", response_model=schemas.PlayerResponse)
async def update_player(
    player_id: int,
    player: schemas.PlayerUpdate,
    db: Session = Depends(get_db)
):
    updated_player = crud.update_player(db=db, player_id=player_id, player=player)
    if not updated_player:
        raise HTTPException(status_code=404, detail="Player not found")
    return updated_player


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(
    player_id: int,
    db: Session = Depends(get_db)
):
    success = crud.delete_player(db=db, player_id=player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")


# Note endpoints
@app.post("/api/notes", response_model=schemas.NoteResponse, status_code=201)
async def create_note(
    note: schemas.NoteCreate,
    db: Session = Depends(get_db)
):
    # Verify player exists
    player = crud.get_player(db=db, player_id=note.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return crud.create_note(db=db, note=note)


@app.get("/api/notes", response_model=List[schemas.NoteResponse])
async def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    player_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_important: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    notes = crud.get_notes(
        db=db,
        skip=skip,
        limit=limit,
        player_id=player_id,
        search=search,
        tag=tag,
        is_important=is_important
    )
    return notes


@app.get("/api/notes/{note_id}", response_model=schemas.NoteResponse)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    note = crud.get_note(db=db, note_id=note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/api/notes/{note_id}", response_model=schemas.NoteResponse)
async def update_note(
    note_id: int,
    note: schemas.NoteUpdate,
    db: Session = Depends(get_db)
):
    updated_note = crud.update_note(db=db, note_id=note_id, note=note)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    return updated_note


@app.delete("/api/notes/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    success = crud.delete_note(db=db, note_id=note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")


# Seed endpoint (optional)
@app.post("/api/seed")
async def seed_data(db: Session = Depends(get_db)):
    # Check if data already exists
    existing_players = crud.get_players(db=db, limit=1)
    if existing_players:
        return {"message": "Database already contains data"}

    # Create sample players
    sample_players = [
        {
            "name": "Stephen Curry",
            "position": "Point Guard",
            "team": "Golden State Warriors",
            "jersey_number": 30,
            "height": "6'2\"",
            "weight": "185 lbs",
            "age": 35
        },
        {
            "name": "LeBron James",
            "position": "Small Forward",
            "team": "Los Angeles Lakers",
            "jersey_number": 23,
            "height": "6'9\"",
            "weight": "250 lbs",
            "age": 39
        },
        {
            "name": "Kevin Durant",
            "position": "Small Forward",
            "team": "Phoenix Suns",
            "jersey_number": 35,
            "height": "6'10\"",
            "weight": "240 lbs",
            "age": 35
        }
    ]

    created_players = []
    for player_data in sample_players:
        player = crud.create_player(db=db, player=schemas.PlayerCreate(**player_data))
        created_players.append(player)

    # Create sample notes
    sample_notes = [
        {
            "player_id": created_players[0].id,
            "title": "Exceptional 3-point shooting",
            "content": "Curry demonstrated incredible range and accuracy from beyond the arc. Made 7/10 three-pointers with defenders in his face.",
            "tags": "shooting, offense, clutch",
            "game_date": "2024-01-15",
            "is_important": True
        },
        {
            "player_id": created_players[0].id,
            "title": "Ball handling under pressure",
            "content": "Showed elite ball handling skills when double-teamed. Able to create space and find open teammates.",
            "tags": "playmaking, ball-handling",
            "game_date": "2024-01-15",
            "is_important": False
        },
        {
            "player_id": created_players[1].id,
            "title": "Leadership and court vision",
            "content": "LeBron's basketball IQ was on full display. Made several key passes that led to easy buckets. Vocal leader on both ends.",
            "tags": "leadership, playmaking, IQ",
            "game_date": "2024-01-16",
            "is_important": True
        }
    ]

    for note_data in sample_notes:
        crud.create_note(db=db, note=schemas.NoteCreate(**note_data))

    return {
        "message": "Database seeded successfully",
        "players_created": len(created_players),
        "notes_created": len(sample_notes)
    }


# Week 2: RAG endpoints
@app.post("/api/rag/retrieve", response_model=RetrievalResponse)
async def retrieve_notes_endpoint(
    request: RetrievalRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieve relevant notes using hybrid search (keyword + semantic).
    Returns ranked snippets with provenance metadata.
    """
    results = retrieve_notes(
        query=request.query,
        db=db,
        player_id=request.player_id,
        team=request.team,
        top_k=request.top_k,
        keyword_weight=request.keyword_weight or 0.4,
        semantic_weight=request.semantic_weight or 0.6
    )

    return RetrievalResponse(
        query=request.query,
        results=results,
        total_results=len(results)
    )


@app.post("/api/rag/generate", response_model=GenerationResponse)
async def generate_answer_endpoint(
    request: GenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate grounded answer with citations using Google Gemini.
    Returns answer, citations, and confidence assessment.
    """
    response = generation.generate_answer(
        query=request.query,
        db=db,
        player_id=request.player_id,
        team=request.team,
        top_k=request.top_k,
        include_retrieval=request.include_retrieval
    )

    return response


# Week 3: AI Assistant endpoints
@app.post("/api/assistant/conversations", response_model=schemas.ConversationResponse, status_code=201)
async def create_conversation(db: Session = Depends(get_db)):
    """Create a new conversation with the AI assistant"""
    conversation = models.Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@app.get("/api/assistant/conversations", response_model=List[schemas.ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all conversations"""
    conversations = (
        db.query(models.Conversation)
        .order_by(models.Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return conversations


@app.get("/api/assistant/conversations/{conversation_id}", response_model=schemas.ConversationResponse)
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get a specific conversation with all its runs"""
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@app.post("/api/assistant/chat")
async def chat_with_assistant(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with the AI assistant using Server-Sent Events for real-time updates.
    Returns a stream of events showing the assistant's progress.
    """
    from app.assistant.agent import AssistantAgent

    # Get or create conversation
    conversation_id = request.conversation_id
    if conversation_id:
        conversation = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = models.Conversation()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Create a new run
    run = models.Run(
        conversation_id=conversation.id,
        user_message=request.message,
        status="running"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Cache IDs before closing the session
    run_id = run.id
    conv_id = conversation.id

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    db.commit()

    async def event_generator():
        """Generate Server-Sent Events for the assistant's progress"""
        try:
            # Send initial event with run info
            yield f"data: {json.dumps({'type': 'run_started', 'run_id': run_id, 'conversation_id': conv_id})}\n\n"

            # Create and run the agent (it will manage its own database session)
            agent = AssistantAgent(run_id=run_id, max_iterations=10)

            # Stream progress updates
            for update in agent.run_agent():
                yield f"data: {json.dumps(update)}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            # Send error event
            error_data = {
                "type": "error",
                "error": str(e),
                "status": "failed"
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/assistant/runs/{run_id}", response_model=schemas.RunResponse)
async def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get a specific run with all its steps"""
    run = db.query(models.Run).filter(models.Run.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return run
