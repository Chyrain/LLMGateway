import React from 'react';
import { JsonView, darkStyles, defaultStyles } from 'react-json-view-lite';
import 'react-json-view-lite/dist/index.css';

const JsonHighlight = ({ data, style = 'light' }) => {
  // Parse string to JSON if needed
  let jsonData = data;
  if (typeof data === 'string') {
    try {
      jsonData = JSON.parse(data);
    } catch {
      return <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{data}</pre>;
    }
  }

  const customStyles = {
    ...defaultStyles,
    container: 'json-view-container',
    basicChildStyle: 'json-child',
    label: 'json-label',
    value: 'json-value',
    string: 'json-string',
    boolean: 'json-boolean',
    number: 'json-number',
    null: 'json-null',
    punctuation: 'json-punctuation',
    collapseIcon: 'json-icon',
    expandIcon: 'json-icon',
  };

  return (
    <div className={`json-highlight-wrapper ${style}`}>
      <JsonView 
        data={jsonData} 
        style={customStyles}
        shouldExpandNode={() => true}
      />
    </div>
  );
};

export default JsonHighlight;
