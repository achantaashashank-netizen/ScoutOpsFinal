import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: ReactNode;
}

function Layout({ children }: LayoutProps) {
  return (
    <div className="layout">
      <header className="header">
        <div className="container">
          <div className="header-content">
            <Link to="/" className="logo">
              <span className="logo-icon">🏀</span>
              <span className="logo-text">ScoutOps</span>
            </Link>
            <nav className="nav">
              <Link to="/" className="nav-link">Players</Link>
              <Link to="/ask" className="nav-link">Ask ScoutOps</Link>
            </nav>
          </div>
        </div>
      </header>
      <main className="main">
        <div className="container">
          {children}
        </div>
      </main>
      <footer className="footer">
        <div className="container">
          <p>&copy; 2025 ScoutOps - NBA Scouting Platform</p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
