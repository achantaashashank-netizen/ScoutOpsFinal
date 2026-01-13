"""
Tool definitions for the AI assistant.
Tools allow the assistant to interact with ScoutOps data.
"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.rag.retrieval import retrieve_notes


# Tool function definitions
def search_players(db: Session, query: str = "", team: str = None, position: str = None) -> Dict[str, Any]:
    """Search for players by name, team, or position"""
    try:
        players = crud.get_players(
            db=db,
            search=query if query else None,
            team=team,
            position=position,
            limit=20
        )

        result = []
        for player in players:
            result.append({
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team": player.team,
                "jersey_number": player.jersey_number,
                "age": player.age
            })

        return {
            "success": True,
            "players": result,
            "count": len(result)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_player_details(db: Session, player_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific player including their notes"""
    try:
        player = crud.get_player(db=db, player_id=player_id)
        if not player:
            return {"success": False, "error": f"Player with ID {player_id} not found"}

        notes = []
        for note in player.notes:
            notes.append({
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "game_date": note.game_date,
                "is_important": note.is_important,
                "created_at": str(note.created_at)
            })

        return {
            "success": True,
            "player": {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team": player.team,
                "jersey_number": player.jersey_number,
                "height": player.height,
                "weight": player.weight,
                "age": player.age
            },
            "notes": notes,
            "notes_count": len(notes)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_notes(db: Session, query: str, player_id: int = None, team: str = None, top_k: int = 5) -> Dict[str, Any]:
    """Search notes using hybrid semantic + keyword search"""
    try:
        # Convert numeric parameters to int in case Gemini sends them as float
        top_k = int(top_k) if top_k is not None else 5
        player_id = int(player_id) if player_id is not None else None

        results = retrieve_notes(
            query=query,
            db=db,
            player_id=player_id,
            team=team,
            top_k=top_k
        )

        formatted_results = []
        for result in results:
            formatted_results.append({
                "note_id": result.note_id,
                "player_name": result.player_name,
                "title": result.title,
                "excerpt": result.excerpt,
                "tags": result.tags,
                "game_date": result.game_date,
                "relevance_score": round(result.relevance_score, 3),
                "keyword_score": round(result.keyword_score, 3),
                "semantic_score": round(result.semantic_score, 3)
            })

        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_note(
    db: Session,
    player_id: int,
    title: str,
    content: str,
    tags: str = None,
    game_date: str = None,
    is_important: bool = False
) -> Dict[str, Any]:
    """Create a new scouting note for a player"""
    try:
        # Verify player exists
        player = crud.get_player(db=db, player_id=player_id)
        if not player:
            return {"success": False, "error": f"Player with ID {player_id} not found"}

        note_data = schemas.NoteCreate(
            player_id=player_id,
            title=title,
            content=content,
            tags=tags,
            game_date=game_date,
            is_important=is_important
        )

        note = crud.create_note(db=db, note=note_data)

        return {
            "success": True,
            "note": {
                "id": note.id,
                "player_id": note.player_id,
                "player_name": player.name,
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "game_date": note.game_date,
                "is_important": note.is_important
            },
            "message": f"Successfully created note for {player.name}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_note(
    db: Session,
    note_id: int,
    title: str = None,
    content: str = None,
    tags: str = None,
    game_date: str = None,
    is_important: bool = None
) -> Dict[str, Any]:
    """Update an existing note"""
    try:
        # Build update data
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content
        if tags is not None:
            update_data["tags"] = tags
        if game_date is not None:
            update_data["game_date"] = game_date
        if is_important is not None:
            update_data["is_important"] = is_important

        if not update_data:
            return {"success": False, "error": "No fields to update"}

        note_update = schemas.NoteUpdate(**update_data)
        note = crud.update_note(db=db, note_id=note_id, note=note_update)

        if not note:
            return {"success": False, "error": f"Note with ID {note_id} not found"}

        return {
            "success": True,
            "note": {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "game_date": note.game_date,
                "is_important": note.is_important
            },
            "message": f"Successfully updated note {note_id}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_player(
    db: Session,
    name: str,
    position: str = None,
    team: str = None,
    jersey_number: int = None,
    height: str = None,
    weight: str = None,
    age: int = None
) -> Dict[str, Any]:
    """Create a new player profile"""
    try:
        player_data = schemas.PlayerCreate(
            name=name,
            position=position,
            team=team,
            jersey_number=jersey_number,
            height=height,
            weight=weight,
            age=age
        )

        player = crud.create_player(db=db, player=player_data)

        return {
            "success": True,
            "player": {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "team": player.team,
                "jersey_number": player.jersey_number,
                "height": player.height,
                "weight": player.weight,
                "age": player.age
            },
            "message": f"Successfully created player profile for {player.name}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Tool definitions for Gemini function calling
TOOL_DEFINITIONS = [
    {
        "name": "search_players",
        "description": "Search for players by name, team, or position. Use this when the user asks about finding players or wants to know which players are in the system.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for player name"
                },
                "team": {
                    "type": "string",
                    "description": "Filter by team name"
                },
                "position": {
                    "type": "string",
                    "description": "Filter by position (e.g., 'Point Guard', 'Small Forward')"
                }
            }
        }
    },
    {
        "name": "get_player_details",
        "description": "Get detailed information about a specific player including all their scouting notes. Use this when you need to see all notes for a particular player.",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The ID of the player"
                }
            },
            "required": ["player_id"]
        }
    },
    {
        "name": "search_notes",
        "description": "Search scouting notes using semantic and keyword search. Use this to find notes about specific topics, skills, or game situations across all players or for a specific player/team.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing what to look for in notes"
                },
                "player_id": {
                    "type": "integer",
                    "description": "Optional: limit search to notes for a specific player"
                },
                "team": {
                    "type": "string",
                    "description": "Optional: limit search to notes for players on a specific team"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_note",
        "description": "Create a new scouting note for a player. Use this when the user wants to add observations, insights, or game notes about a player.",
        "parameters": {
            "type": "object",
            "properties": {
                "player_id": {
                    "type": "integer",
                    "description": "The ID of the player this note is about"
                },
                "title": {
                    "type": "string",
                    "description": "Brief title for the note"
                },
                "content": {
                    "type": "string",
                    "description": "Detailed content of the scouting note"
                },
                "tags": {
                    "type": "string",
                    "description": "Optional comma-separated tags (e.g., 'shooting, defense, playmaking')"
                },
                "game_date": {
                    "type": "string",
                    "description": "Optional date of the game observed (YYYY-MM-DD format)"
                },
                "is_important": {
                    "type": "boolean",
                    "description": "Mark as important/priority note"
                }
            },
            "required": ["player_id", "title", "content"]
        }
    },
    {
        "name": "update_note",
        "description": "Update an existing scouting note. Use this to edit or modify note details.",
        "parameters": {
            "type": "object",
            "properties": {
                "note_id": {
                    "type": "integer",
                    "description": "The ID of the note to update"
                },
                "title": {
                    "type": "string",
                    "description": "New title for the note"
                },
                "content": {
                    "type": "string",
                    "description": "New content for the note"
                },
                "tags": {
                    "type": "string",
                    "description": "Updated tags"
                },
                "game_date": {
                    "type": "string",
                    "description": "Updated game date"
                },
                "is_important": {
                    "type": "boolean",
                    "description": "Updated importance flag"
                }
            },
            "required": ["note_id"]
        }
    },
    {
        "name": "create_player",
        "description": "Create a new player profile. Use this when the user wants to add a new player to track.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Player's full name"
                },
                "position": {
                    "type": "string",
                    "description": "Player's position"
                },
                "team": {
                    "type": "string",
                    "description": "Player's team"
                },
                "jersey_number": {
                    "type": "integer",
                    "description": "Jersey number"
                },
                "height": {
                    "type": "string",
                    "description": "Height (e.g., '6\\'2\"')"
                },
                "weight": {
                    "type": "string",
                    "description": "Weight (e.g., '185 lbs')"
                },
                "age": {
                    "type": "integer",
                    "description": "Player's age"
                }
            },
            "required": ["name"]
        }
    }
]


# Map tool names to functions
TOOL_FUNCTIONS = {
    "search_players": search_players,
    "get_player_details": get_player_details,
    "search_notes": search_notes,
    "create_note": create_note,
    "update_note": update_note,
    "create_player": create_player
}


def execute_tool(tool_name: str, tool_args: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Execute a tool function by name with the given arguments"""
    if tool_name not in TOOL_FUNCTIONS:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    try:
        tool_func = TOOL_FUNCTIONS[tool_name]
        result = tool_func(db=db, **tool_args)
        return result
    except TypeError as e:
        return {"success": False, "error": f"Invalid arguments for {tool_name}: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}
