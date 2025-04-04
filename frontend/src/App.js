import React, { useState } from 'react';
import { Shield, Upload, Link as LinkIcon } from 'lucide-react';
import './App.css';

function App() {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState(null); 
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("Processing...");

    const formData = new FormData();
    if (url) formData.append("url", url);
    if (file) formData.append("crx_file", file);

    try {
      const response = await fetch("http://localhost:8080/api/analyze/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (data.status === "success") {
        setMessage(`File processed: ${data.file_path}`);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError("Failed to connect to the server.");
    }
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="logo-container">
            <Shield className="logo-icon" />
            <span className="logo-text">ExterminAI</span>
          </div>
          <div className="nav-links">
            <a href="#" className="nav-link">Home</a>
            <a href="#" className="nav-link">About</a>
            <a href="#" className="nav-link">Documentation</a>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <div className="content-card">
          <h1 className="page-title">
            AI Detection of Malicious Browser Extensions
          </h1>

          <form onSubmit={handleSubmit} className="form-container">
            <div className="input-group">
              <LinkIcon className="input-icon" />
              <input
                type="text"
                placeholder="Enter Chrome Web Store URL"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="url-input"
              />
            </div>

            <label className="file-upload">
              <div className="file-upload-content">
                <Upload className="h-6 w-6 text-gray-500" />
                <span className="text-sm text-gray-600">
                  {file ? file.name : "Upload CRX File"}
                </span>
              </div>
              <input
                type="file"
                accept=".crx"
                onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                className="hidden"
              />
            </label>

            <button type="submit" className="submit-button">
              Analyze
            </button>
          </form>

          {error && (
            <div className="error-message">
              <p>Error: {error}</p>
            </div>
          )}
          
          {message && (
            <div className="success-message">
              <p>{message}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
