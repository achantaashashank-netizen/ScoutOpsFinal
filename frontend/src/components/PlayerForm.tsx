import { useState, FormEvent } from 'react';
import { PlayerCreate, PlayerUpdate, Player } from '../types';
import './Form.css';

interface PlayerFormProps {
  player?: Player;
  onSubmit: (data: PlayerCreate | PlayerUpdate) => Promise<void>;
  onCancel: () => void;
}

function PlayerForm({ player, onSubmit, onCancel }: PlayerFormProps) {
  const [formData, setFormData] = useState({
    name: player?.name || '',
    position: player?.position || '',
    team: player?.team || '',
    jersey_number: player?.jersey_number?.toString() || '',
    height: player?.height || '',
    weight: player?.weight || '',
    age: player?.age?.toString() || '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data: PlayerCreate | PlayerUpdate = {
        name: formData.name,
        position: formData.position || undefined,
        team: formData.team || undefined,
        jersey_number: formData.jersey_number ? parseInt(formData.jersey_number) : undefined,
        height: formData.height || undefined,
        weight: formData.weight || undefined,
        age: formData.age ? parseInt(formData.age) : undefined,
      };

      await onSubmit(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save player');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form">
      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label htmlFor="name" className="form-label">
          Name <span className="required">*</span>
        </label>
        <input
          id="name"
          type="text"
          className="input"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="position" className="form-label">
            Position
          </label>
          <input
            id="position"
            type="text"
            className="input"
            value={formData.position}
            onChange={(e) => setFormData({ ...formData, position: e.target.value })}
            placeholder="e.g., Point Guard"
          />
        </div>

        <div className="form-group">
          <label htmlFor="team" className="form-label">
            Team
          </label>
          <input
            id="team"
            type="text"
            className="input"
            value={formData.team}
            onChange={(e) => setFormData({ ...formData, team: e.target.value })}
            placeholder="e.g., Lakers"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="jersey_number" className="form-label">
            Jersey #
          </label>
          <input
            id="jersey_number"
            type="number"
            className="input"
            value={formData.jersey_number}
            onChange={(e) => setFormData({ ...formData, jersey_number: e.target.value })}
            placeholder="23"
          />
        </div>

        <div className="form-group">
          <label htmlFor="height" className="form-label">
            Height
          </label>
          <input
            id="height"
            type="text"
            className="input"
            value={formData.height}
            onChange={(e) => setFormData({ ...formData, height: e.target.value })}
            placeholder="6'2&quot;"
          />
        </div>

        <div className="form-group">
          <label htmlFor="weight" className="form-label">
            Weight
          </label>
          <input
            id="weight"
            type="text"
            className="input"
            value={formData.weight}
            onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
            placeholder="185 lbs"
          />
        </div>

        <div className="form-group">
          <label htmlFor="age" className="form-label">
            Age
          </label>
          <input
            id="age"
            type="number"
            className="input"
            value={formData.age}
            onChange={(e) => setFormData({ ...formData, age: e.target.value })}
            placeholder="25"
          />
        </div>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn btn-secondary" disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving...' : player ? 'Update Player' : 'Create Player'}
        </button>
      </div>
    </form>
  );
}

export default PlayerForm;
