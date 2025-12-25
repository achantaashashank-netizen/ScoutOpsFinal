export interface Player {
  id: number;
  name: string;
  position: string | null;
  team: string | null;
  jersey_number: number | null;
  height: string | null;
  weight: string | null;
  age: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface PlayerDetail extends Player {
  notes: Note[];
}

export interface Note {
  id: number;
  player_id: number;
  title: string;
  content: string;
  tags: string | null;
  game_date: string | null;
  is_important: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface PlayerCreate {
  name: string;
  position?: string;
  team?: string;
  jersey_number?: number;
  height?: string;
  weight?: string;
  age?: number;
}

export interface PlayerUpdate {
  name?: string;
  position?: string;
  team?: string;
  jersey_number?: number;
  height?: string;
  weight?: string;
  age?: number;
}

export interface NoteCreate {
  player_id: number;
  title: string;
  content: string;
  tags?: string;
  game_date?: string;
  is_important?: boolean;
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  tags?: string;
  game_date?: string;
  is_important?: boolean;
}
