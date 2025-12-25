import { useState, FormEvent } from 'react';
import { NoteCreate, NoteUpdate, Note } from '../types';
import './Form.css';

interface NoteFormProps {
  note?: Note;
  playerId?: number;
  onSubmit: (data: NoteCreate | NoteUpdate) => Promise<void>;
  onCancel: () => void;
}

function NoteForm({ note, playerId, onSubmit, onCancel }: NoteFormProps) {
  const [formData, setFormData] = useState({
    title: note?.title || '',
    content: note?.content || '',
    tags: note?.tags || '',
    game_date: note?.game_date || '',
    is_important: note?.is_important || false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data: NoteCreate | NoteUpdate = note
        ? {
            title: formData.title,
            content: formData.content,
            tags: formData.tags || undefined,
            game_date: formData.game_date || undefined,
            is_important: formData.is_important,
          }
        : {
            player_id: playerId!,
            title: formData.title,
            content: formData.content,
            tags: formData.tags || undefined,
            game_date: formData.game_date || undefined,
            is_important: formData.is_important,
          };

      await onSubmit(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save note');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form">
      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label htmlFor="title" className="form-label">
          Title <span className="required">*</span>
        </label>
        <input
          id="title"
          type="text"
          className="input"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="content" className="form-label">
          Content <span className="required">*</span>
        </label>
        <textarea
          id="content"
          className="textarea"
          value={formData.content}
          onChange={(e) => setFormData({ ...formData, content: e.target.value })}
          required
          rows={6}
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="tags" className="form-label">
            Tags
          </label>
          <input
            id="tags"
            type="text"
            className="input"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            placeholder="shooting, defense, clutch"
          />
          <small className="form-hint">Comma-separated tags</small>
        </div>

        <div className="form-group">
          <label htmlFor="game_date" className="form-label">
            Game Date
          </label>
          <input
            id="game_date"
            type="text"
            className="input"
            value={formData.game_date}
            onChange={(e) => setFormData({ ...formData, game_date: e.target.value })}
            placeholder="2024-01-15"
          />
        </div>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={formData.is_important}
            onChange={(e) => setFormData({ ...formData, is_important: e.target.checked })}
          />
          <span>Mark as important</span>
        </label>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn btn-secondary" disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving...' : note ? 'Update Note' : 'Create Note'}
        </button>
      </div>
    </form>
  );
}

export default NoteForm;
