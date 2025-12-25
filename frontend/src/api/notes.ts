import apiClient from './client';
import { Note, NoteCreate, NoteUpdate } from '../types';

export const notesApi = {
  getAll: async (params?: {
    player_id?: number;
    search?: string;
    tag?: string;
    is_important?: boolean;
  }): Promise<Note[]> => {
    const response = await apiClient.get('/api/notes', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Note> => {
    const response = await apiClient.get(`/api/notes/${id}`);
    return response.data;
  },

  create: async (note: NoteCreate): Promise<Note> => {
    const response = await apiClient.post('/api/notes', note);
    return response.data;
  },

  update: async (id: number, note: NoteUpdate): Promise<Note> => {
    const response = await apiClient.put(`/api/notes/${id}`, note);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/notes/${id}`);
  },
};
