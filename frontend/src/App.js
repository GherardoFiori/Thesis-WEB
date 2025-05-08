import React from 'react';
import './App.css';
import { Routes, Route, Link } from 'react-router-dom';
import Home from './Home';
import About from './About';
import Help from './Help';

function App() {
  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="navbar-content">
          <Link to="/" className="logo-container">
            <img src="/ExterminAI logo.png" alt="ExterminAI Logo" className="logo-image" />
          </Link>
          <div className="nav-links">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/about" className="nav-link">About</Link>
            <Link to="/help" className="nav-link">Help</Link>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </main>

      <footer className="footer">
      <h5>ExterminAI © 2025</h5>
        <a href="https://github.com/GherardoFiori/AI-detection-of-malicious-browser-extensions" target="_blank" rel="noopener noreferrer" className="github-link">
          <img src="/github.png" alt="GitHub" className="github-icon" />
        </a>
      </footer>
    </div>

    
  );
}

export default App;
