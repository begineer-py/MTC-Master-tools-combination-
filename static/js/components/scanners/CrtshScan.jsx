import React from 'react';
import ScanComponent from '../common/ScanComponent';
import CrtshResult from './CrtshResult';
import useScan from '../../hooks/useScan';

const CrtshScan = ({ userId, targetId }) => {
  const scanEndpoint = (userId, targetId) => `/api/crtsh/scan/${userId}/${targetId}`;
  
  const {
    isScanning,
    status,
    error,
    startScan
  } = useScan(scanEndpoint);

  const handleScanClick = async () => {
    try {
      await startScan(userId, targetId);
    } catch (error) {
      console.error('CRT.sh 掃描錯誤:', error);
    }
  };

  return (
    <div className="scan-section">
      <ScanComponent
        title="CRT.sh"
        isScanning={isScanning}
        status={status}
        error={error}
        onScanClick={handleScanClick}
        renderResult={null}
      />

      <CrtshResult userId={userId} targetId={targetId} />
    </div>
  );
};

export default CrtshScan; 