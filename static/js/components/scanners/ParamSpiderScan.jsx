import React, { useState } from 'react';
import ScanComponent from '../common/ScanComponent';
import ParamSpiderResult from './ParamSpiderResult';
import useScan from '../../hooks/useScan';

const ParamSpiderScan = ({ userId, targetId }) => {
  const scanEndpoint = (userId, targetId) => `/api/paramspider/scan/${userId}/${targetId}`;
  
  const {
    isScanning,
    status,
    error,
    startScan
  } = useScan(scanEndpoint);

  const handleScanClick = async () => {
    try {
      await startScan(userId, targetId, {
        body: {
          exclude: '',
          threads: 50
        }
      });
    } catch (error) {
      console.error('ParamSpider 掃描錯誤:', error);
    }
  };

  return (
    <div className="scan-section">
      <ScanComponent
        title="ParamSpider"
        isScanning={isScanning}
        status={status}
        error={error}
        onScanClick={handleScanClick}
        renderResult={null}
      />

      <ParamSpiderResult userId={userId} targetId={targetId} />
    </div>
  );
};

export default ParamSpiderScan; 