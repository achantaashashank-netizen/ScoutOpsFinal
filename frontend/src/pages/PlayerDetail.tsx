import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { playersApi } from '../api/players';
import { notesApi } from '../api/notes';
import { PlayerDetail as PlayerDetailType, Note, NoteCreate, NoteUpdate, PlayerUpdate } from '../types';
import NoteCard from '../components/NoteCard';
import Modal from '../components/Modal';
import NoteForm from '../components/NoteForm';
import PlayerForm from '../components/PlayerForm';
import './PlayerDetail.css';

function PlayerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [player, setPlayer] = useState<PlayerDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);
  const [isEditPlayerModalOpen, setIsEditPlayerModalOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchPlayer = async () => {
    try {
      setLoading(true);
      const data = await playersApi.getById(Number(id));
      setPlayer(data);
      setError('');
    } catch (err: any) {
      setError('Failed to load player');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlayer();
  }, [id]);

  const handleCreateNote = async (data: NoteCreate) => {
    await notesApi.create(data);
    setIsNoteModalOpen(false);
    fetchPlayer();
  };

  const handleUpdateNote = async (data: NoteUpdate) => {
    if (editingNote) {
      await notesApi.update(editingNote.id, data);
      setEditingNote(null);
      fetchPlayer();
    }
  };

  const handleDeleteNote = async (noteId: number) => {
    if (window.confirm('Are you sure you want to delete this note?')) {
      try {
        await notesApi.delete(noteId);
        fetchPlayer();
      } catch (err) {
        alert('Failed to delete note');
      }
    }
  };

  const handleUpdatePlayer = async (data: PlayerUpdate) => {
    await playersApi.update(Number(id), data);
    setIsEditPlayerModalOpen(false);
    fetchPlayer();
  };

  const handleDeletePlayer = async () => {
    if (window.confirm(`Are you sure you want to delete ${player?.name}? This will also delete all associated notes.`)) {
      try {
        await playersApi.delete(Number(id));
        navigate('/');
      } catch (err) {
        alert('Failed to delete player');
      }
    }
  };

  if (loading) {
    return <div className="loading">Loading player...</div>;
  }

  if (error || !player) {
    return (
      <div className="error-container">
        <div className="error">{error || 'Player not found'}</div>
        <Link to="/" className="btn btn-primary">
          Back to Players
        </Link>
      </div>
    );
  }

  const filteredNotes = player.notes.filter(
    (note) =>
      note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      note.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      note.tags?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="player-detail-page">
      <div className="breadcrumb">
        <Link to="/" className="breadcrumb-link">
          Players
        </Link>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">{player.name}</span>
      </div>

      <div className="player-header-card">
        <div className="player-header-content">
          <div className="player-header-avatar">
            {player.jersey_number || '?'}
          </div>
          <div className="player-header-info">
            <h1 className="player-header-name">{player.name}</h1>
            <p className="player-header-team">{player.team || 'No team'}</p>
          </div>
        </div>

        <div className="player-stats-grid">
          {player.position && (
            <div className="stat-item">
              <span className="stat-label">Position</span>
              <span className="stat-value">{player.position}</span>
            </div>
          )}
          {player.height && (
            <div className="stat-item">
              <span className="stat-label">Height</span>
              <span className="stat-value">{player.height}</span>
            </div>
          )}
          {player.weight && (
            <div className="stat-item">
              <span className="stat-label">Weight</span>
              <span className="stat-value">{player.weight}</span>
            </div>
          )}
          {player.age && (
            <div className="stat-item">
              <span className="stat-label">Age</span>
              <span className="stat-value">{player.age}</span>
            </div>
          )}
        </div>

        <div className="player-actions">
          <button onClick={() => setIsEditPlayerModalOpen(true)} className="btn btn-secondary">
            Edit Player
          </button>
          <button onClick={handleDeletePlayer} className="btn btn-danger">
            Delete Player
          </button>
        </div>
      </div>

      <div className="notes-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Scouting Notes</h2>
            <p className="section-subtitle">
              {player.notes.length} {player.notes.length === 1 ? 'note' : 'notes'}
            </p>
          </div>
          <button onClick={() => setIsNoteModalOpen(true)} className="btn btn-success">
            + Add Note
          </button>
        </div>

        {player.notes.length > 0 && (
          <div className="search-bar">
            <input
              type="text"
              className="input search-input"
              placeholder="Search notes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        )}

        {filteredNotes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <h3 className="empty-state-title">
              {player.notes.length === 0 ? 'No notes yet' : 'No matching notes'}
            </h3>
            <p className="empty-state-description">
              {player.notes.length === 0
                ? `Start documenting your observations about ${player.name}`
                : 'Try adjusting your search terms'}
            </p>
            {player.notes.length === 0 && (
              <button onClick={() => setIsNoteModalOpen(true)} className="btn btn-success">
                Add First Note
              </button>
            )}
          </div>
        ) : (
          <div className="notes-grid">
            {filteredNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onEdit={setEditingNote}
                onDelete={handleDeleteNote}
              />
            ))}
          </div>
        )}
      </div>

      <Modal
        isOpen={isNoteModalOpen}
        onClose={() => setIsNoteModalOpen(false)}
        title="Add New Note"
      >
        <NoteForm
          playerId={player.id}
          onSubmit={handleCreateNote}
          onCancel={() => setIsNoteModalOpen(false)}
        />
      </Modal>

      <Modal
        isOpen={editingNote !== null}
        onClose={() => setEditingNote(null)}
        title="Edit Note"
      >
        {editingNote && (
          <NoteForm
            note={editingNote}
            onSubmit={handleUpdateNote}
            onCancel={() => setEditingNote(null)}
          />
        )}
      </Modal>

      <Modal
        isOpen={isEditPlayerModalOpen}
        onClose={() => setIsEditPlayerModalOpen(false)}
        title="Edit Player"
      >
        <PlayerForm
          player={player}
          onSubmit={handleUpdatePlayer}
          onCancel={() => setIsEditPlayerModalOpen(false)}
        />
      </Modal>
    </div>
  );
}

export default PlayerDetail;
