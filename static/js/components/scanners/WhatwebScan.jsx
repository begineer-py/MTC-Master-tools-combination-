import React from 'react';
import ScanComponent from '../common/ScanComponent';
import useScan from '../../hooks/useScan';
import { formatWhatwebResults } from '../../utils/formatResults';

const WhatwebScan = ({ userId, targetId }) => {
  const scanEndpoint = (userId, targetId) => `/user/${userId}/whatweb/${targetId}`;
  
  const {
    isScanning,
    status,
    result,
    error,
    startScan
  } = useScan(scanEndpoint, formatWhatwebResults);

  const handleScanClick = async () => {
    try {
      await startScan(userId, targetId);
    } catch (error) {
      console.error('Whatweb 掃描錯誤:', error);
    }
  };

  const renderResult = (result) => {
    return (
      <div className="whatweb-results">
        <div className="result-header">
          <h3>Whatweb 掃描結果</h3>
          <div className="result-info">
            <p><strong>掃描時間:</strong> {result.scan_time}</p>
            <p><strong>目標:</strong> {result.target}</p>
          </div>
        </div>

        <div className="plugins-list">
          <table className="tech-table">
            <thead>
              <tr>
                <th>插件名稱</th>
                <th>版本/詳情</th>
                <th>置信度</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(result.plugins).map(([plugin, details], index) => (
                <tr key={index}>
                  <td className="plugin-name">{plugin}</td>
                  <td className="plugin-version">
                    {Array.isArray(details.version) 
                      ? details.version.join(', ') 
                      : details.version || '未知'}
                  </td>
                  <td className="plugin-certainty">
                    {details.certainty ? `${details.certainty}%` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {result.error && (
          <div className="scan-error">
            <p><strong>警告:</strong> {result.error}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <ScanComponent
      title="Whatweb"
      isScanning={isScanning}
      status={status}
      error={error}
      result={result}
      onScanClick={handleScanClick}
      renderResult={renderResult}
    />
  );
};

export default WhatwebScan; 