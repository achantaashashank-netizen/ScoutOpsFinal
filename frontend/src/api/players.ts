import apiClient from './client';
import { Player, PlayerDetail, PlayerCreate, PlayerUpdate } from '../types';

export const playersApi = {
  getAll: async (params?: {
    search?: string;
    team?: string;
    position?: string;
  }): Promise<Player[]> => {
    const response = await apiClient.get('/api/players', { params });
    return response.data;
  },

  getById: async (id: number): Promise<PlayerDetail> => {
    const response = await apiClient.get(`/api/players/${id}`);
    return response.data;
  },

  create: async (player: PlayerCreate): Promise<Player> => {
    const response = await apiClient.post('/api/players', player);
    return response.data;
  },

  update: async (id: number, player: PlayerUpdate): Promise<Player> => {
    const response = await apiClient.put(`/api/players/${id}`, player);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/players/${id}`);
  },
};
