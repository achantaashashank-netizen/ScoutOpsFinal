import { Link } from 'react-router-dom';
import { Player } from '../types';
import './PlayerCard.css';

interface PlayerCardProps {
  player: Player;
}

function PlayerCard({ player }: PlayerCardProps) {
  return (
    <Link to={`/players/${player.id}`} className="player-card">
      <div className="player-card-header">
        <div className="player-avatar">
          {player.jersey_number || '?'}
        </div>
        <div className="player-info">
          <h3 className="player-name">{player.name}</h3>
          <p className="player-team">{player.team || 'No team'}</p>
        </div>
      </div>
      <div className="player-card-body">
        <div className="player-stat">
          <span className="stat-label">Position</span>
          <span className="stat-value">{player.position || 'N/A'}</span>
        </div>
        {player.height && (
          <div className="player-stat">
            <span className="stat-label">Height</span>
            <span className="stat-value">{player.height}</span>
          </div>
        )}
        {player.age && (
          <div className="player-stat">
            <span className="stat-label">Age</span>
            <span className="stat-value">{player.age}</span>
          </div>
        )}
      </div>
    </Link>
  );
}

export default PlayerCard;
