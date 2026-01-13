# AI Assistant Testing Guide

## Test the AI Assistant

Once all services are running, you can test the AI Assistant at:
- **Frontend URL**: http://localhost:3000/assistant
- **API URL**: http://localhost:8000/api/assistant/chat

### Test Scenarios

#### 1. Basic Player Search
**Input**: "Show me all players in the system"
**Expected**: Assistant should use `search_players` tool and return a list of all players

#### 2. Search Specific Notes
**Input**: "Find notes about shooting"
**Expected**: Assistant should use `search_notes` tool with semantic search

#### 3. Create a New Note
**Input**: "Add a note for Stephen Curry: Exceptional off-ball movement, creates space with constant motion"
**Expected**:
- Assistant should search for Stephen Curry's player ID
- Then create a note using `create_note` tool
- Confirm the note was created

#### 4. Multi-Step Task
**Input**: "Create a note for LeBron James about his defensive presence in the paint"
**Expected**:
- Search for LeBron James
- Get player details
- Create the note
- Confirm success

#### 5. Query with Context
**Input**: "What are the notes about Golden State Warriors players?"
**Expected**: Search notes filtered by team "Golden State Warriors"

#### 6. Error Handling
**Input**: "Add a note for a player named XYZ123"
**Expected**: Assistant should search, find no player, and report error gracefully

### Manual API Testing with curl

```bash
# Test conversation creation
curl -X POST http://localhost:8000/api/assistant/conversations

# Test chat (streaming)
curl -X POST http://localhost:8000/api/assistant/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all players"}' \
  --no-buffer

# Get conversation history
curl http://localhost:8000/api/assistant/conversations/1
```

### Monitoring

Watch the logs to see the assistant working:

```bash
# Backend logs (see tool calls and steps)
docker-compose logs backend -f

# All services
docker-compose logs -f
```

### Expected Behavior

1. **Real-time Step Updates**: You should see steps appearing live as the assistant works:
   - "Analyzing your request..." (thinking)
   - "Calling search_players..." (tool_call)
   - "Calling create_note..." (tool_call)
   - Final response with summary

2. **Multi-Step Reasoning**: The assistant can chain multiple tool calls:
   - Search for player → Get player ID → Create note with that ID

3. **Error Recovery**: If a tool fails, the assistant should:
   - Report the error
   - Try alternative approaches if possible
   - Provide helpful feedback

4. **Conversation Memory**: The assistant remembers previous messages in the same conversation

### Troubleshooting

If the assistant doesn't work:

1. **Check Backend Logs**:
   ```bash
   docker-compose logs backend --tail=50
   ```
   Look for errors related to Gemini API, database, or Qdrant

2. **Verify Database Migration**:
   ```bash
   docker-compose exec backend python -c "from app.database import engine; from sqlalchemy import inspect; inspector = inspect(engine); print(inspector.get_table_names())"
   ```
   Should include: conversations, runs, run_steps

3. **Test API Health**:
   ```bash
   curl http://localhost:8000/health
   ```

4. **Check Google API Key**:
   ```bash
   docker-compose exec backend python -c "from app.config import get_settings; print('API Key set:', bool(get_settings().google_api_key))"
   ```

5. **Verify Qdrant Connection**:
   ```bash
   curl http://localhost:6333/collections/scout_notes
   ```

### Features Implemented

✅ **Real-time streaming** - Live step updates using Server-Sent Events
✅ **Tool/Function calling** - 6 tools available (search_players, get_player_details, search_notes, create_note, update_note, create_player)
✅ **Multi-step reasoning** - Agent can chain multiple tool calls
✅ **Conversation tracking** - All runs and steps stored in database
✅ **Error handling** - Graceful failure with retries
✅ **Beautiful UI** - Chat panel with step visualization
✅ **Bounded execution** - Max 10 iterations to prevent infinite loops

### Next Steps

After testing, you can:
- Add more tools (delete note, generate reports, etc.)
- Improve prompts for better reasoning
- Add authentication/authorization
- Implement conversation persistence across browser sessions
- Add file upload for player photos or game footage analysis
