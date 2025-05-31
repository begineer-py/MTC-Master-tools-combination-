import React from 'react';
import useScan from '../../hooks/useScan';
import ScanComponent from '../common/ScanComponent';
import WebtechResult from './WebtechResult';

const WebtechScan = ({ targetId }) => {
  const scanEndpoint = (targetId) => `/api/webtech/scan/${targetId}`;
  const { isScanning, status, error, startScan } = useScan(scanEndpoint);

  const handleScanClick = async () => {
    try {
      await startScan(targetId);
    } catch (err) {
      console.error('Webtech掃描錯誤:', err);
    }
  };

  const renderResult = () => {
    return <WebtechResult targetId={targetId} />;
  };

  return (
    <div className="webtech-scan">
      <ScanComponent
        title="Web技術識別"
        description="識別目標網站使用的Web技術、框架和服務器信息"
        onScanClick={handleScanClick}
        isScanning={isScanning}
        status={status}
        error={error}
        renderResult={renderResult}
      />
    </div>
  );
};

export default WebtechScan; 