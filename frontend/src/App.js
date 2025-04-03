import React, { useState } from "react";
import "./App.css";

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
    <div className="container">
      <header>
        <img src="/logo.png" alt="Logo" className="logo" />
        <h1>AI Detection of Malicious Browser Extensions</h1>
      </header>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter Chrome Web Store URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <label className="file-upload">
          Upload CRX File
          <input type="file" accept=".crx" onChange={(e) => setFile(e.target.files[0])} />
        </label>
        <button type="submit">Analyze</button>
      </form>
      {error && <div className="error">Error: {error}</div>}
      {message && <div className="message">{message}</div>}
    </div>
  );
}

export default App;
