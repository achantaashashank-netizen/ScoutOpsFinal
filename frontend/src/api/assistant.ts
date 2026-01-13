import apiClient from './client';

export interface Conversation {
  id: number;
  created_at: string;
  updated_at?: string;
  runs: Run[];
}

export interface Run {
  id: number;
  conversation_id: number;
  user_message: string;
  status: string;
  assistant_response?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  steps: RunStep[];
}

export interface RunStep {
  id: number;
  step_number: number;
  step_type: string;
  description: string;
  tool_name?: string;
  tool_input?: string;
  tool_output?: string;
  status: string;
  error_message?: string;
  created_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: number;
}

export interface StreamEvent {
  type: string;
  [key: string]: any;
}

export const assistantAPI = {
  createConversation: async (): Promise<Conversation> => {
    const response = await apiClient.post('/assistant/conversations');
    return response.data;
  },

  getConversation: async (conversationId: number): Promise<Conversation> => {
    const response = await apiClient.get(`/assistant/conversations/${conversationId}`);
    return response.data;
  },

  listConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get('/assistant/conversations');
    return response.data;
  },

  getRun: async (runId: number): Promise<Run> => {
    const response = await apiClient.get(`/assistant/runs/${runId}`);
    return response.data;
  },

  // Stream chat using EventSource (Server-Sent Events)
  streamChat: (request: ChatRequest, onEvent: (event: StreamEvent) => void, onError: (error: Error) => void) => {
    const params = new URLSearchParams();
    if (request.conversation_id) {
      params.append('conversation_id', request.conversation_id.toString());
    }

    // Create EventSource with POST data via URL encoding (since EventSource only supports GET)
    // We'll need to use fetch with ReadableStream instead
    const url = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/assistant/chat`;

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('Response body is not readable');
        }

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode the chunk
          const chunk = decoder.decode(value);

          // Split by newlines to handle multiple events
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // Remove 'data: ' prefix

              if (data.trim()) {
                try {
                  const event = JSON.parse(data);
                  onEvent(event);
                } catch (e) {
                  console.error('Error parsing SSE data:', e, data);
                }
              }
            }
          }
        }
      })
      .catch((error) => {
        onError(error);
      });
  },
};
