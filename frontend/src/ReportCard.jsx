import React from 'react';
import './ReportCard.css'; 

const ReportCard = ({ verdict, confidence, features }) => {
  if (!verdict || !features) return null;

  const featureEntries = Object.entries(features);

  return (
    <div className="report-card">
      <h2 className={`verdict ${verdict}`}>
        Verdict: {verdict.toUpperCase()} ({Math.round(confidence * 100)}% confidence)
      </h2>

      <table className="feature-table">
        <thead>
          <tr>
            <th>Feature</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {featureEntries.map(([key, value]) => (
            <tr key={key}>
              <td>{key}</td>
              <td>{typeof value === 'boolean' ? (value ? '✔️' : '❌') : value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ReportCard;
