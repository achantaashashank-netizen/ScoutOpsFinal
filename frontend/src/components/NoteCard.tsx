import { Note } from '../types';
import './NoteCard.css';

interface NoteCardProps {
  note: Note;
  onEdit: (note: Note) => void;
  onDelete: (id: number) => void;
}

function NoteCard({ note, onEdit, onDelete }: NoteCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const tags = note.tags ? note.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  return (
    <div className={`note-card ${note.is_important ? 'note-card-important' : ''}`}>
      <div className="note-card-header">
        <h3 className="note-title">{note.title}</h3>
        {note.is_important && (
          <span className="important-badge">Important</span>
        )}
      </div>

      <p className="note-content">{note.content}</p>

      {tags.length > 0 && (
        <div className="note-tags">
          {tags.map((tag, index) => (
            <span key={index} className="tag">
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="note-meta">
        {note.game_date && (
          <span className="note-date">Game: {note.game_date}</span>
        )}
        <span className="note-date">Created: {formatDate(note.created_at)}</span>
      </div>

      <div className="note-actions">
        <button onClick={() => onEdit(note)} className="btn btn-secondary btn-sm">
          Edit
        </button>
        <button onClick={() => onDelete(note.id)} className="btn btn-danger btn-sm">
          Delete
        </button>
      </div>
    </div>
  );
}

export default NoteCard;
