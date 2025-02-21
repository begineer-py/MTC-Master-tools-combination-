import React, { useState } from 'react';
import ScanComponent from '../common/ScanComponent';
import NmapResult from './NmapResult';
import useScan from '../../hooks/useScan';
import { formatNmapResults } from '../../utils/formatResults';

const NmapScan = ({ userId, targetId }) => {
  const [scanType, setScanType] = useState('common'); // 'common' 或 'full'
  const scanEndpoint = (userId, targetId) => `/api/nmap/scan/${userId}/${targetId}`;
  
  const {
    isScanning,
    status,
    result,
    error,
    startScan
  } = useScan(scanEndpoint, formatNmapResults);

  const handleScanClick = async () => {
    try {
      await startScan(userId, targetId, {
        body: {
          scan_type: scanType
        }
      });
    } catch (error) {
      console.error('Nmap 掃描錯誤:', error);
    }
  };

  return (
    <div className="scan-section">
      <div className="scan-options">
        <select 
          value={scanType} 
          onChange={(e) => setScanType(e.target.value)}
          className="scan-type-select"
        >
          <option value="common">常見端口掃描</option>
          <option value="full">完整端口掃描</option>
        </select>
      </div>

      <ScanComponent
        title="Nmap"
        isScanning={isScanning}
        status={status}
        error={error}
        result={result}
        onScanClick={handleScanClick}
        renderResult={null}
      />

      <NmapResult userId={userId} targetId={targetId} />
    </div>
  );
};

export default NmapScan; 