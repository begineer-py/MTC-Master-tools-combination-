import React from 'react';
import Loading from './Loading';
import Notification from './Notification';

const ScanComponent = ({
  title,
  isScanning,
  status,
  error,
  result,
  onScanClick,
  renderResult,
  buttonText
}) => {
  return (
    <div className="scan-section">
      <button 
        onClick={onScanClick}
        disabled={isScanning}
        className="scan-button"
      >
        {buttonText || `開始${title}掃描`}
      </button>
      
      <div className={`scan-status ${error ? 'error' : ''}`}>
        {status}
      </div>
      
      {isScanning && <Loading text={`${title}掃描中...`} />}
      
      {error && (
        <div className="error-message">
          <h4>掃描失敗</h4>
          <p>{error}</p>
          <p>如果問題持續存在，請稍後重試或聯繫管理員</p>
        </div>
      )}
      
      {result && renderResult(result)}
      
      {error && (
        <Notification
          message={`${title}掃描失敗: ${error}`}
          type="error"
          duration={5000}
        />
      )}
    </div>
  );
};

export default ScanComponent; 