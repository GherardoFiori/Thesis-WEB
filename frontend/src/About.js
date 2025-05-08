import React from 'react';

function About() {
  return (
    <div className="page-container">
      <h1>About ExterminAI</h1>
      <p>
        <strong>ExterminAI</strong> is an AI-powered tool designed to identify potentially malicious browser extensions. With the increasing number of browser add-ons, it's critical to ensure that extensions you install are safe, secure, and trustworthy.
      </p>

      <p>
        Built as part of a research and development initiative, ExterminAI analyzes Chrome extension files (<code>.crx</code>) or URLs from the Chrome Web Store using a machine learning backend. It extracts behavioral features and evaluates the likelihood of malicious intent based on trained AI models.
      </p>

      <p>
        Whether you're a user concerned about your privacy, a researcher analyzing extension security, or a developer testing your own tools, ExterminAI offers a fast and easy way to get an intelligent risk assessment.
      </p>

      <p>
        This project combines cybersecurity principles with modern AI to bring meaningful, automated insights to end users and professionals alike.
      </p>
    </div>
  );
}

export default About;
