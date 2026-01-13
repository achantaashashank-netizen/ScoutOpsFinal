import { useState, useEffect, useRef } from 'react';
import { assistantAPI, type Run, type RunStep, type StreamEvent } from '../api/assistant';
import './ChatPanel.css';

interface ChatPanelProps {
  conversationId?: number;
  onConversationCreated?: (id: number) => void;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  runId?: number;
  steps?: RunStep[];
  status?: string;
  error?: string;
}

function ChatPanel({ conversationId: initialConversationId, onConversationCreated }: ChatPanelProps) {
  const [conversationId, setConversationId] = useState<number | undefined>(initialConversationId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSteps, setCurrentSteps] = useState<RunStep[]>([]);
  const [currentRunId, setCurrentRunId] = useState<number | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentSteps]);

  useEffect(() => {
    // Load conversation history if conversation ID is provided
    if (conversationId) {
      loadConversation();
    }
  }, [conversationId]);

  const loadConversation = async () => {
    if (!conversationId) return;

    try {
      const conversation = await assistantAPI.getConversation(conversationId);
      const loadedMessages: Message[] = [];

      for (const run of conversation.runs) {
        loadedMessages.push({
          role: 'user',
          content: run.user_message,
        });

        if (run.assistant_response) {
          loadedMessages.push({
            role: 'assistant',
            content: run.assistant_response,
            runId: run.id,
            steps: run.steps,
            status: run.status,
          });
        } else if (run.error_message) {
          loadedMessages.push({
            role: 'assistant',
            content: run.error_message,
            runId: run.id,
            status: 'failed',
            error: run.error_message,
          });
        }
      }

      setMessages(loadedMessages);
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);
    setCurrentSteps([]);
    setCurrentRunId(undefined);

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: userMessage,
      },
    ]);

    try {
      // Stream the assistant's response
      assistantAPI.streamChat(
        {
          message: userMessage,
          conversation_id: conversationId,
        },
        (event: StreamEvent) => {
          handleStreamEvent(event);
        },
        (error: Error) => {
          console.error('Stream error:', error);
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `Error: ${error.message}`,
              status: 'failed',
              error: error.message,
            },
          ]);
          setIsLoading(false);
          setCurrentSteps([]);
        }
      );
    } catch (error: any) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error.message}`,
          status: 'failed',
          error: error.message,
        },
      ]);
      setIsLoading(false);
      setCurrentSteps([]);
    }
  };

  const handleStreamEvent = (event: StreamEvent) => {
    switch (event.type) {
      case 'run_started':
        if (!conversationId && event.conversation_id) {
          setConversationId(event.conversation_id);
          onConversationCreated?.(event.conversation_id);
        }
        setCurrentRunId(event.run_id);
        break;

      case 'step':
        // Update current steps
        setCurrentSteps((prev) => {
          const existing = prev.find((s) => s.id === event.step.id);
          if (existing) {
            // Update existing step
            return prev.map((s) => (s.id === event.step.id ? event.step : s));
          } else {
            // Add new step
            return [...prev, event.step];
          }
        });
        break;

      case 'final_response':
        // Add assistant message
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: event.response,
            runId: currentRunId,
            steps: currentSteps,
            status: event.status,
          },
        ]);
        setCurrentSteps([]);
        setIsLoading(false);
        break;

      case 'error':
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${event.error}`,
            runId: currentRunId,
            steps: currentSteps,
            status: 'failed',
            error: event.error,
          },
        ]);
        setCurrentSteps([]);
        setIsLoading(false);
        break;

      case 'done':
        setIsLoading(false);
        break;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>AI Assistant</h2>
        <p className="chat-subtitle">Ask questions, search notes, or create new data</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="empty-icon">🤖</div>
            <h3>Welcome to ScoutOps AI Assistant</h3>
            <p>I can help you with:</p>
            <ul className="capabilities-list">
              <li>Search for players and notes</li>
              <li>Create new scouting notes</li>
              <li>Answer questions about player data</li>
              <li>Update existing notes</li>
              <li>Add new players to the system</li>
            </ul>
            <p className="start-prompt">Try asking: "Show me all players" or "Find notes about shooting"</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message message-${message.role}`}>
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>

              {message.steps && message.steps.length > 0 && (
                <div className="message-steps">
                  <details>
                    <summary>View steps ({message.steps.length})</summary>
                    <div className="steps-list">
                      {message.steps.map((step) => (
                        <div key={step.id} className={`step step-${step.status}`}>
                          <div className="step-header">
                            <span className="step-type">{step.step_type}</span>
                            <span className={`step-status status-${step.status}`}>{step.status}</span>
                          </div>
                          <div className="step-description">{step.description}</div>
                          {step.tool_name && (
                            <div className="step-tool">
                              <strong>Tool:</strong> {step.tool_name}
                            </div>
                          )}
                          {step.tool_output && (
                            <details className="step-output">
                              <summary>Output</summary>
                              <pre>{step.tool_output}</pre>
                            </details>
                          )}
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {message.error && (
                <div className="message-error">
                  <strong>Error:</strong> {message.error}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="message-loading">
                <div className="loading-spinner"></div>
                <span>Thinking...</span>
              </div>

              {currentSteps.length > 0 && (
                <div className="current-steps">
                  {currentSteps.map((step) => (
                    <div key={step.id} className={`step step-${step.status}`}>
                      <div className="step-header">
                        <span className="step-type">{step.step_type}</span>
                        <span className={`step-status status-${step.status}`}>
                          {step.status === 'running' ? (
                            <span className="status-spinner">⏳</span>
                          ) : step.status === 'completed' ? (
                            '✓'
                          ) : (
                            '✗'
                          )}
                        </span>
                      </div>
                      <div className="step-description">{step.description}</div>
                      {step.tool_name && (
                        <div className="step-tool">
                          <strong>Tool:</strong> {step.tool_name}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about your scouting data..."
          rows={2}
          disabled={isLoading}
        />
        <button className="chat-send-button" onClick={handleSend} disabled={!input.trim() || isLoading}>
          {isLoading ? '⏳' : '➤'}
        </button>
      </div>
    </div>
  );
}

export default ChatPanel;
