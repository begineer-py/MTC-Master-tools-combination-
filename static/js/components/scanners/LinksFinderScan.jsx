import React, { useState } from 'react';
import ScanComponent from '../common/ScanComponent';
import useScan from '../../hooks/useScan';

const LinksFinderScan = ({ userId, targetId }) => {
  const scanEndpoint = `/api/linksfinder/scan/${userId}/${targetId}`;
  const { isScanning, status, error, startScan, result } = useScan();
  
  const handleScan = async () => {
    try {
      await startScan(scanEndpoint, {});
    } catch (err) {
      console.error('启动扫描失败:', err);
    }
  };

  return (
    <ScanComponent 
      scanData={result} 
      scanStatus={status} 
      scanError={error} 
      scanLoading={isScanning} 
      onScanClick={handleScan}
    />
  );
};

export default LinksFinderScan;
