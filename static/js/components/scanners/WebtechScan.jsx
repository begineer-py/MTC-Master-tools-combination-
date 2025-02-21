import React, { useEffect, useCallback, useState } from 'react';
import ScanComponent from '../common/ScanComponent';
import useScan from '../../hooks/useScan';
import { formatWebtechResults } from '../../utils/formatResults';

const WebtechScan = ({ userId, targetId }) => {
  const [hasResult, setHasResult] = useState(false);
  const scanEndpoint = useCallback((userId, targetId) => `/api/webtech/scan/${userId}/${targetId}`, []);
  const resultEndpoint = useCallback((userId, targetId) => `/api/webtech/result/${userId}/${targetId}`, []);
  
  const {
    isScanning,
    status,
    result,
    error,
    startScan,
    setResult,
    setStatus,
    setError
  } = useScan(scanEndpoint, formatWebtechResults);

  const fetchLatestResult = useCallback(async () => {
    try {
      const response = await fetch(resultEndpoint(userId, targetId), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'same-origin'
      });

      const data = await response.json();
      console.log('獲取到的結果數據:', data);
      
      if (response.ok && data.status === 'success' && data.result) {
        const formattedResult = formatWebtechResults(data.result);
        console.log('格式化後的結果:', formattedResult);
        setResult(formattedResult);
        setStatus('已加載最新掃描結果');
        setHasResult(true);  // 設置有結果的標誌
      }
    } catch (error) {
      console.error('加載結果錯誤:', error);
      setError('加載結果失敗');
    }
  }, [userId, targetId, resultEndpoint, setResult, setStatus, setError]);

  useEffect(() => {
    fetchLatestResult();
  }, [fetchLatestResult]);

  const handleScanClick = useCallback(async () => {
    try {
      const scanResult = await startScan(userId, targetId);
      console.log('掃描結果:', scanResult);
      if (scanResult && scanResult.status === 'success') {
        setHasResult(true);
      }
    } catch (error) {
      console.error('Web 技術掃描錯誤:', error);
    }
  }, [userId, targetId, startScan]);

  const handleDownload = useCallback(async (format) => {
    try {
      window.location.href = `/api/webtech/download/${userId}/${targetId}?format=${format}`;
    } catch (error) {
      console.error('下載錯誤:', error);
    }
  }, [userId, targetId]);

  const renderDownloadButtons = () => (
    <div className="result-actions" style={{ marginTop: '10px' }}>
      <button onClick={() => handleDownload('txt')} className="download-button">
        下載 TXT
      </button>
      <button onClick={() => handleDownload('csv')} className="download-button">
        下載 CSV
      </button>
      <button onClick={() => handleDownload('json')} className="download-button">
        下載 JSON
      </button>
    </div>
  );

  const renderResult = useCallback((result) => {
    console.log('渲染結果函數被調用，結果數據:', result);
    
    if (!result) {
      console.log('沒有結果數據');
      return (
        <div className="webtech-results">
          <div className="result-header">
            <h3>Web 技術掃描結果</h3>
            <div className="result-info">
              <p>沒有檢測到技術信息</p>
            </div>
          </div>
        </div>
      );
    }

    if (!result.technologies || Object.keys(result.technologies).length === 0) {
      console.log('有結果但沒有技術信息');
      return (
        <div className="webtech-results">
          <div className="result-header">
            <h3>Web 技術掃描結果</h3>
            <div className="result-info">
              <p>沒有檢測到技術信息</p>
            </div>
          </div>
        </div>
      );
    }

    console.log('有完整的結果數據，包含技術信息');
    return (
      <div className="webtech-results">
        <div className="result-header">
          <h3>Web 技術掃描結果</h3>
          <div className="result-info">
            <p><strong>目標網站:</strong> {result.target_url}</p>
            <p><strong>掃描時間:</strong> {result.scan_time}</p>
          </div>
        </div>
        
        {Object.entries(result.technologies).map(([category, technologies]) => (
          <div key={category} className="tech-category">
            <h4>{category}</h4>
            <table className="tech-table">
              <thead>
                <tr>
                  <th>技術名稱</th>
                  <th>版本</th>
                  <th>置信度</th>
                </tr>
              </thead>
              <tbody>
                {technologies.map((tech, index) => (
                  <tr key={index}>
                    <td>{tech.name}</td>
                    <td>{tech.version}</td>
                    <td>{tech.confidence}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    );
  }, []);

  return (
    <div className="scan-section">
      <ScanComponent
        title="Web 技術"
        isScanning={isScanning}
        status={status}
        error={error}
        result={result}
        onScanClick={handleScanClick}
        renderResult={renderResult}
      />
      {hasResult && !isScanning && renderDownloadButtons()}
    </div>
  );
};

export default WebtechScan; 