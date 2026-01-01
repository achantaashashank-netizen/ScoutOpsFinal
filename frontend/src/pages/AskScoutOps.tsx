import { useState } from 'react';
import { ragApi } from '../api/rag';
import type { GenerationResponse } from '../types/rag';
import AnswerDisplay from '../components/AnswerDisplay';
import CitationCard from '../components/CitationCard';
import './AskScoutOps.css';

function AskScoutOps() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<GenerationResponse | null>(null);
  const [activeCitation, setActiveCitation] = useState<number | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await ragApi.generate({
        query: query.trim(),
        top_k: 5,
        include_retrieval: false, // Keep UI simple - no debug view
      });

      setResponse(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate answer. Please try again.');
      console.error('Error generating answer:', err);
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    "What are Stephen Curry's strengths?",
    "How does Curry perform under pressure?",
    "What are LeBron's leadership qualities?",
  ];

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className="ask-scoutops-container">
      <div className="ask-scoutops-header">
        <h1>Ask ScoutOps</h1>
        <p>Ask questions about players and get answers grounded in your scouting notes</p>
      </div>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about a player..."
            className="search-input"
            disabled={loading}
          />
          <button
            type="submit"
            className="search-button"
            disabled={loading || !query.trim()}
          >
            {loading ? 'Searching...' : 'Ask'}
          </button>
        </div>

        {!response && !loading && (
          <div className="example-queries">
            <p className="example-label">Try asking:</p>
            <div className="example-buttons">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleExampleClick(example)}
                  className="example-button"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Analyzing scouting notes...</p>
        </div>
      )}

      {response && !loading && (
        <div className="results-container">
          <AnswerDisplay
            answer={response.answer}
            citations={response.citations}
            confidence={response.confidence}
            hasSufficientInfo={response.has_sufficient_information}
            onCitationClick={setActiveCitation}
          />

          {response.citations.length > 0 && (
            <div className="citations-section">
              <h2>Sources</h2>
              <div className="citations-list">
                {response.citations.map((citation) => (
                  <CitationCard
                    key={citation.note_id}
                    citation={citation}
                    isActive={activeCitation === citation.reference_number}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AskScoutOps;
