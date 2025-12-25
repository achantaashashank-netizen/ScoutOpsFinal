import { useState, useEffect } from 'react';
import { playersApi } from '../api/players';
import { Player, PlayerCreate } from '../types';
import PlayerCard from '../components/PlayerCard';
import Modal from '../components/Modal';
import PlayerForm from '../components/PlayerForm';
import './PlayerList.css';

function PlayerList() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      const data = await playersApi.getAll({ search: searchTerm || undefined });
      setPlayers(data);
      setError('');
    } catch (err: any) {
      setError('Failed to load players');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlayers();
  }, [searchTerm]);

  const handleCreatePlayer = async (data: PlayerCreate) => {
    await playersApi.create(data);
    setIsModalOpen(false);
    fetchPlayers();
  };

  return (
    <div className="player-list-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Players</h1>
          <p className="page-subtitle">Manage your scouting roster</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          + Add Player
        </button>
      </div>

      <div className="search-bar">
        <input
          type="text"
          className="input search-input"
          placeholder="Search players by name, team, or position..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="loading">Loading players...</div>
      ) : players.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏀</div>
          <h3 className="empty-state-title">No players found</h3>
          <p className="empty-state-description">
            {searchTerm
              ? 'Try adjusting your search terms'
              : 'Get started by adding your first player'}
          </p>
          {!searchTerm && (
            <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
              Add Your First Player
            </button>
          )}
        </div>
      ) : (
        <div className="players-grid">
          {players.map((player) => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Player"
      >
        <PlayerForm
          onSubmit={handleCreatePlayer}
          onCancel={() => setIsModalOpen(false)}
        />
      </Modal>
    </div>
  );
}

export default PlayerList;
