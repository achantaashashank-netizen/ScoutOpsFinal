"""
AI Assistant Agent with tool calling and multi-step reasoning.
Uses Google Gemini for natural language understanding and response generation.
"""
import json
from typing import Generator, Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import google.generativeai as genai

from app.config import get_settings
from app import models
from app.assistant.tools import TOOL_DEFINITIONS, execute_tool
from app.database import SessionLocal


settings = get_settings()
genai.configure(api_key=settings.google_api_key)


class AssistantAgent:
    """
    AI Assistant that can perform multi-step actions using tools.
    Tracks progress and streams updates in real-time.
    """

    def __init__(self, run_id: int, max_iterations: int = 10):
        self.run_id = run_id
        self.max_iterations = max_iterations
        self.current_step = 0

        # Create our own database session for this agent
        self.db = SessionLocal()

        # Load the run to get initial data
        run = self.db.query(models.Run).filter(models.Run.id == run_id).first()
        if not run:
            self.db.close()
            raise ValueError(f"Run {run_id} not found")

        # Cache run attributes to avoid session issues - don't keep the run object
        self.conversation_id = run.conversation_id
        self.user_message = run.user_message

        # Prepare tools for function calling
        self.tools = self._convert_tools_to_gemini_format()

        # Initialize Gemini model with tools - using gemini-2.5-flash (has 20/day quota vs 0 for lite)
        self.model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash',
            tools=self.tools
        )

    def _convert_tools_to_gemini_format(self) -> List[Dict]:
        """Convert our tool definitions to Gemini's function declaration format"""
        gemini_tools = []

        for tool in TOOL_DEFINITIONS:
            gemini_tools.append({
                "function_declarations": [{
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }]
            })

        return gemini_tools

    def _create_step(
        self,
        step_type: str,
        description: str,
        tool_name: str = None,
        tool_input: str = None,
        tool_output: str = None,
        status: str = "running"
    ) -> tuple:
        """Create a new step in the run - returns (step_id, step_dict)"""
        self.current_step += 1

        step = models.RunStep(
            run_id=self.run_id,
            step_number=self.current_step,
            step_type=step_type,
            description=description,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            status=status
        )

        self.db.add(step)
        self.db.flush()  # Flush to get the ID without closing the session

        # Store the step ID
        step_id = step.id

        # Make a detached copy for safe access
        step_dict = {
            'id': step.id,
            'step_number': step.step_number,
            'step_type': step.step_type,
            'description': step.description,
            'tool_name': step.tool_name,
            'tool_input': step.tool_input,
            'tool_output': step.tool_output,
            'status': step.status,
            'error_message': step.error_message,
            'created_at': step.created_at.isoformat() if step.created_at else None
        }

        self.db.commit()
        return step_id, step_dict

    def _update_step(self, step_id: int, status: str, tool_output: str = None, error: str = None):
        """Update an existing step by re-querying it from the database"""
        # Re-query the step to get a fresh session-bound object
        step = self.db.query(models.RunStep).filter(models.RunStep.id == step_id).first()
        if not step:
            raise ValueError(f"Step {step_id} not found")

        step.status = status
        if tool_output is not None:
            step.tool_output = tool_output
        if error is not None:
            step.error_message = error

        # Make a detached copy before committing
        step_dict = {
            'id': step.id,
            'step_number': step.step_number,
            'step_type': step.step_type,
            'description': step.description,
            'tool_name': step.tool_name,
            'tool_input': step.tool_input,
            'tool_output': step.tool_output,
            'status': step.status,
            'error_message': step.error_message,
            'created_at': step.created_at.isoformat() if step.created_at else None
        }

        self.db.commit()
        return step_dict

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the assistant"""
        return """You are ScoutOps AI Assistant, an intelligent helper for basketball scouts and analysts.

Your capabilities:
- Search and analyze player data and scouting notes
- Create and update scouting notes with detailed observations
- Find relevant information using semantic search
- Perform multi-step tasks to accomplish user goals

Guidelines:
1. Be concise and professional in your responses
2. Use tools when you need to read or modify data
3. When creating notes, be detailed and specific
4. Always confirm actions that modify data (create/update)
5. If you're unsure about player IDs, search first
6. Provide helpful context from the data you retrieve

When users ask you to perform actions:
1. Think through the steps needed
2. Use the appropriate tools
3. Provide clear feedback on what you did
4. Summarize the results

Remember: You have access to real data in ScoutOps. Use your tools to help users effectively."""

    def run_agent(self) -> Generator[Dict[str, Any], None, None]:
        """
        Execute the agent loop with tool calling.
        Yields step updates as they happen for real-time streaming.
        """
        try:
            # Step 1: Start thinking
            thinking_step_id, thinking_step_dict = self._create_step(
                step_type="thinking",
                description="Analyzing your request...",
                status="running"
            )
            yield {"type": "step", "step": thinking_step_dict}

            # Build conversation history
            conversation_history = self._build_conversation_history()

            # Add system prompt and user message
            messages = [
                {"role": "user", "parts": [self._build_system_prompt()]},
                {"role": "model", "parts": ["I understand. I'm ScoutOps AI Assistant and I'll help you with player scouting data using my available tools."]},
            ]

            # Add conversation history
            messages.extend(conversation_history)

            # Add current user message
            messages.append({
                "role": "user",
                "parts": [self.user_message]
            })

            # Complete thinking step
            updated_thinking = self._update_step(thinking_step_id, status="completed")
            yield {"type": "step", "step": updated_thinking}

            # Start chat session
            chat = self.model.start_chat(history=messages[:-1])

            # Send user message and iterate
            response = chat.send_message(messages[-1]["parts"][0])

            iteration = 0
            final_response = None

            while iteration < self.max_iterations:
                iteration += 1

                # Check if model wants to use tools
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        # Check for function call
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            tool_name = func_call.name
                            tool_args = dict(func_call.args)

                            # Create tool call step
                            tool_step_id, tool_step_dict = self._create_step(
                                step_type="tool_call",
                                description=f"Calling {tool_name}...",
                                tool_name=tool_name,
                                tool_input=json.dumps(tool_args, indent=2),
                                status="running"
                            )
                            yield {"type": "step", "step": tool_step_dict}

                            # Execute the tool
                            try:
                                tool_result = execute_tool(tool_name, tool_args, self.db)
                                tool_output = json.dumps(tool_result, indent=2)

                                updated_tool_step = self._update_step(tool_step_id, status="completed", tool_output=tool_output)
                                yield {"type": "step", "step": updated_tool_step}

                                # Send tool result back to model
                                response = chat.send_message({
                                    "function_response": {
                                        "name": tool_name,
                                        "response": tool_result
                                    }
                                })

                            except Exception as e:
                                error_msg = f"Tool execution error: {str(e)}"
                                failed_tool_step = self._update_step(tool_step_id, status="failed", error=error_msg)
                                yield {"type": "step", "step": failed_tool_step}
                                raise

                        # Check for text response
                        elif hasattr(part, 'text') and part.text:
                            final_response = part.text
                            break

                # If we have a final text response, we're done
                if final_response:
                    break

                # Safety check
                if iteration >= self.max_iterations:
                    raise Exception("Maximum iterations reached")

            # Create final response step
            if final_response:
                response_step_id, response_step_dict = self._create_step(
                    step_type="response",
                    description="Generating response...",
                    status="completed"
                )
                yield {"type": "step", "step": response_step_dict}

                # Update run with final response
                run = self.db.query(models.Run).filter(models.Run.id == self.run_id).first()
                if run:
                    run.status = "completed"
                    run.assistant_response = final_response
                    run.completed_at = datetime.utcnow()
                    self.db.commit()

                yield {
                    "type": "final_response",
                    "response": final_response,
                    "status": "completed"
                }
            else:
                raise Exception("No response generated from model")

        except Exception as e:
            # Handle errors
            error_msg = str(e)

            error_step_id, error_step_dict = self._create_step(
                step_type="error",
                description=f"Error: {error_msg}",
                status="failed",
                tool_output=error_msg
            )
            yield {"type": "step", "step": error_step_dict}

            run = self.db.query(models.Run).filter(models.Run.id == self.run_id).first()
            if run:
                run.status = "failed"
                run.error_message = error_msg
                run.completed_at = datetime.utcnow()
                self.db.commit()

            yield {
                "type": "error",
                "error": error_msg,
                "status": "failed"
            }

        finally:
            # Always close the database session
            self.db.close()

    def _build_conversation_history(self) -> List[Dict[str, Any]]:
        """Build conversation history from previous runs in this conversation"""
        history = []

        # Get all previous runs in this conversation
        previous_runs = (
            self.db.query(models.Run)
            .filter(
                models.Run.conversation_id == self.conversation_id,
                models.Run.id < self.run_id,
                models.Run.status == "completed"
            )
            .order_by(models.Run.created_at)
            .limit(5)  # Keep last 5 exchanges for context
            .all()
        )

        for run in previous_runs:
            # Add user message
            history.append({
                "role": "user",
                "parts": [run.user_message]
            })

            # Add assistant response
            if run.assistant_response:
                history.append({
                    "role": "model",
                    "parts": [run.assistant_response]
                })

        return history
