import React, { useState } from 'react';
import { Shield, Upload, Link as LinkIcon } from 'lucide-react';
import './App.css';
import ReportCard from './ReportCard';

function App() {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState(null); 
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [verdict, setVerdict] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [features, setFeatures] = useState(null);

  const getCsrfToken = async () => {
    const response = await fetch("http://localhost:8080/api/csrf/", {
      credentials: 'include'
    });
    const data = await response.json();
    return data.csrfToken;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setVerdict(null); // Reset report
    setIsLoading(true);

    try {
      const csrfToken = await getCsrfToken();
      const formData = new FormData();
      
      if (url) formData.append('url', url);
      if (file) formData.append('crx_file', file);

      const response = await fetch("http://localhost:8080/api/analyze/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken
        },
        credentials: 'include',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message || "Extension analyzed successfully!");

        console.log("Received verdict:", data.verdict);
        console.log("Features:", data.features);

        if (data.verdict) {
          setVerdict(data.verdict);
          setConfidence(data.confidence);
          setFeatures(data.features);
        }
      } else {
        throw new Error(data.message || "Failed to process file");
      }

    } catch (err) {
      setError(err.message || "Failed to connect to server");
      console.error("Submission error:", err);
    } finally {
      setIsLoading(false);
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
                disabled={isLoading}
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
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="hidden"
                disabled={isLoading}
              />
            </label>

            <button 
              type="submit" 
              className="submit-button"
              disabled={isLoading || (!url && !file)}
            >
              {isLoading ? 'Analyzing...' : 'Analyze'}
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

          {verdict && (
            <ReportCard
              verdict={verdict}
              confidence={confidence}
              features={features}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
