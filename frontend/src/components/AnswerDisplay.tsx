import type { Citation } from '../types/rag';

interface AnswerDisplayProps {
  answer: string;
  citations: Citation[];
  confidence: string;
  hasSufficientInfo: boolean;
  onCitationClick: (refNumber: number) => void;
}

function AnswerDisplay({
  answer,
  citations,
  confidence,
  hasSufficientInfo,
  onCitationClick,
}: AnswerDisplayProps) {
  // Parse answer and make citations clickable
  const renderAnswer = () => {
    // Split by citation pattern [1], [2], etc.
    const parts = answer.split(/(\[\d+\])/g);

    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const refNum = parseInt(match[1]);
        return (
          <sup key={index}>
            <a
              href={`#citation-${refNum}`}
              className="citation-link"
              onClick={(e) => {
                e.preventDefault();
                onCitationClick(refNum);
                // Scroll to citation
                document.getElementById(`citation-${refNum}`)?.scrollIntoView({
                  behavior: 'smooth',
                  block: 'center',
                });
              }}
            >
              [{refNum}]
            </a>
          </sup>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  const getConfidenceBadge = () => {
    const colors: Record<string, string> = {
      high: 'confidence-high',
      medium: 'confidence-medium',
      low: 'confidence-low',
    };

    return (
      <span className={`confidence-badge ${colors[confidence] || 'confidence-low'}`}>
        {confidence.toUpperCase()} CONFIDENCE
      </span>
    );
  };

  return (
    <div className="answer-container">
      <div className="answer-header">
        <h2>Answer</h2>
        {getConfidenceBadge()}
      </div>

      {!hasSufficientInfo && (
        <div className="warning-banner">
          ⚠️ Limited information available in scouting notes
        </div>
      )}

      <div className="answer-text">{renderAnswer()}</div>

      {citations.length > 0 && (
        <div className="citations-count">
          Based on {citations.length} scouting note{citations.length > 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}

export default AnswerDisplay;
