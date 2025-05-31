import { useState } from 'react';

const useScan = (endpointFn) => {
  const [isScanning, setIsScanning] = useState(false);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const startScan = async (targetId, options = {}) => {
    if (isScanning) {
      throw new Error('掃描已在進行中');
    }

    try {
      setIsScanning(true);
      setStatus('掃描中，預計需要3-5分鐘...');
      setError(null);

      // 使用endpointFn生成URL
      const url = endpointFn(targetId);
      console.log('請求 URL:', url);
      console.log('請求選項:', options);

      const requestOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'same-origin',
        body: JSON.stringify(options)
      };

      console.log('完整請求配置:', {
        url: url,
        ...requestOptions
      });

      const response = await fetch(url, requestOptions);

      console.log('響應狀態:', response.status);
      console.log('響應頭:', {
        'content-type': response.headers.get('content-type'),
        'status': response.status,
        'statusText': response.statusText
      });

      const data = await response.json();
      console.log('響應數據:', data);

      if (!response.ok) {
        throw new Error(data.message || `掃描失敗 (${response.status})`);
      }

      if (data.success) {
        setStatus('掃描已啟動');
        return data;
      } else {
        throw new Error(data.message || '掃描失敗');
      }

    } catch (err) {
      console.error('掃描錯誤:', {
        message: err.message,
        stack: err.stack,
        type: err.constructor.name
      });
      setError(err.message);
      setStatus('掃描失敗');
      throw err;
    } finally {
      setIsScanning(false);
    }
  };

  return {
    isScanning,
    status,
    result,
    error,
    startScan,
    setResult,
    setStatus,
    setError
  };
};

export default useScan; 