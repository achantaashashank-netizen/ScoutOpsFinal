import { Link } from 'react-router-dom';
import type { Citation } from '../types/rag';

interface CitationCardProps {
  citation: Citation;
  isActive: boolean;
}

function CitationCard({ citation, isActive }: CitationCardProps) {
  return (
    <div
      id={`citation-${citation.reference_number}`}
      className={`citation-card ${isActive ? 'active' : ''}`}
    >
      <div className="citation-header">
        <span className="citation-number">[{citation.reference_number}]</span>
        <Link to={`/players/${citation.note_id}`} className="citation-player">
          {citation.player_name}
        </Link>
      </div>

      <h4 className="citation-title">{citation.title}</h4>

      <p className="citation-excerpt">{citation.excerpt}</p>
    </div>
  );
}

export default CitationCard;
