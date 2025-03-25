import React, { useState } from 'react';

function App() {
  const [result, setResult] = useState('');
  const [file, setFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8080/api/analyze/', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data.result || data.error);
    } catch (err) {
      setResult("Failed to connect to server");
    }
  };

  return (
    <div>
      <h1>Extension Malware Detector</h1>
      <form onSubmit={handleSubmit}>
        <input 
          type="file" 
          onChange={(e) => setFile(e.target.files[0])} 
          accept=".json,.txt" 
        />
        <button type="submit">Analyze</button>
      </form>
      {result && <p>Result: {result}</p>}
    </div>
  );
}

export default App; 