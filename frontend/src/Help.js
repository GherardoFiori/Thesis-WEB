import React from 'react';

function Help() {
  return (
    <div className="page-container">
      <h1>How do you get the URL?</h1>
      <p>To get the URL of the extension you want to analyse simply copy and paste it from the Google Chrome Website.</p>
      <img
        src="/collect URL.gif"
        alt="How to use ExterminAI"
         className="help-gif"
      />
      <br></br>
      <br></br>
      <a
        href="https://chromewebstore.google.com/"
        target="_blank"
        rel="noopener noreferrer"
      >
        Google Chrome Extension Store
      </a>
      <br></br>
      <a
        href="https://addons.mozilla.org/en-US/firefox/extensions/"
        target="_blank"
        rel="noopener noreferrer"
      >
        Firefox Extension Store
      </a>
    </div>
  );
}

export default Help;
