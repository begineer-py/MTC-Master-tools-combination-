import React, { useState } from 'react';
import useScan from '../../hooks/useScan';
import ScanComponent from '../common/ScanComponent';
import NmapResult from './NmapResult';

const NmapScan = ({ targetId }) => {
  const [scanType, setScanType] = useState('common');
  const [scanInitiated, setScanInitiated] = useState(false);

  const scanEndpoint = (targetId) => `/api/nmap/scan/${targetId}`;
  const { isScanning, status, error, startScan } = useScan(scanEndpoint);

  const handleScanClick = async () => {
    try {
      await startScan(targetId, { scan_type: scanType });
      setScanInitiated(true);
    } catch (err) {
      console.error('Nmap掃描錯誤:', err);
    }
  };

  return (
    <div className="nmap-scan">
      <div className="scan-type-selector mb-3">
        <select
          className="form-select"
          value={scanType}
          onChange={(e) => setScanType(e.target.value)}
          disabled={isScanning || scanInitiated}
        >
          <option value="common">常用端口掃描</option>
          <option value="full">完整端口掃描</option>
        </select>
      </div>

      <ScanComponent
        title="Nmap 端口掃描"
        description="使用 Nmap 掃描目標主機的開放端口和服務"
        onScanClick={handleScanClick}
        isScanning={isScanning}
        status={status}
        error={error}
        renderResult={null}
        buttonText={scanInitiated ? '正在獲取結果...' : `開始 Nmap ${scanType === 'common' ? '常用' : '完整'}端口掃描`}
        scanInitiated={scanInitiated}
      />
      
      {scanInitiated && !error && <NmapResult targetId={targetId} />}
      
      {error && (
        <div className="alert alert-danger mt-3">
            Nmap 掃描或結果獲取失敗: {error}
        </div>
      )}
    </div>
  );
};

export default NmapScan; 