import React from 'react';
import Loading from './Loading';
import Notification from './Notification';

const ScanComponent = ({
  title,
  isScanning,
  status,
  error,
  onScanClick,
  buttonText,
  scanInitiated
}) => {
  return (
    <div className="scan-section">
      <button 
        onClick={onScanClick}
        disabled={isScanning || scanInitiated}
        className="scan-button btn btn-primary mb-2"
      >
        {isScanning 
          ? <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> 
          : <i className="fas fa-play me-1"></i>
        }
        {buttonText || `開始${title}掃描`}
      </button>
      
      <div className={`scan-status ${error ? 'text-danger' : (status === 'completed' ? 'text-success' : 'text-info')} mb-2`}>
        {isScanning ? '掃描中...' : 
         scanInitiated ? '等待結果...' : 
         status ? status : '準備就緒'}
      </div>
      
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