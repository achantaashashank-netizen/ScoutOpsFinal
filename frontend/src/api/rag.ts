import { apiClient } from './client';
import type {
  RetrievalRequest,
  RetrievalResponse,
  GenerationRequest,
  GenerationResponse
} from '../types/rag';

export const ragApi = {
  // Retrieve relevant notes using hybrid search
  retrieve: async (request: RetrievalRequest): Promise<RetrievalResponse> => {
    const response = await apiClient.post('/api/rag/retrieve', request);
    return response.data;
  },

  // Generate answer with citations
  generate: async (request: GenerationRequest): Promise<GenerationResponse> => {
    const response = await apiClient.post('/api/rag/generate', request);
    return response.data;
  },
};
