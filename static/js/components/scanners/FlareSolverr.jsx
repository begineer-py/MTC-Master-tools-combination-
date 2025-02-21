import React from 'react';
import ScanComponent from '../common/ScanComponent';
import useScan from '../../hooks/useScan';
import { formatFlareSolverrResults } from '../../utils/formatResults';

const FlareSolverr = ({ userId, targetId }) => {
  const scanEndpoint = (userId, targetId) => `/api/flaresolverr/scan/${userId}/${targetId}`;
  
  const {
    isScanning,
    status,
    result,
    error,
    startScan
  } = useScan(scanEndpoint, formatFlareSolverrResults);

  const handleScanClick = async () => {
    try {
      await startScan(userId, targetId);
    } catch (error) {
      console.error('FlareSolverr 服務錯誤:', error);
    }
  };

  const renderResult = (result) => {
    return (
      <div className="cloudflare-details">
        <h4>服務詳情</h4>
        <div className="result-info">
          <p><strong>版本:</strong> <span className="version">{result.version || 'N/A'}</span></p>
          <p><strong>運行時間:</strong> <span className="uptime">{result.uptime || 'N/A'}</span></p>
          <p><strong>Cloudflare 狀態:</strong> <span className="cloudflare-status">
            {result.is_cloudflare ? '已檢測到' : '未檢測到'}
          </span></p>
          {result.message && (
            <p><strong>消息:</strong> <span className="message">{result.message}</span></p>
          )}
        </div>
      </div>
    );
  };

  return (
    <ScanComponent
      title="FlareSolverr"
      isScanning={isScanning}
      status={status}
      error={error}
      result={result}
      onScanClick={handleScanClick}
      renderResult={renderResult}
      buttonText="啟動 FlareSolverr 服務"
    />
  );
};

export default FlareSolverr; 