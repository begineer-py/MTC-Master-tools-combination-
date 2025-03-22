import { useState } from 'react';

const useScan = () => {
  const [isScanning, setIsScanning] = useState(false);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const startScan = async (endpoint, options = {}) => {
    if (isScanning) {
      throw new Error('掃描已在進行中');
    }

    try {
      setIsScanning(true);
      setStatus('掃描中，預計需要3-5分鐘...');
      setError(null);

      // endpoint 现在是字符串，直接使用
      const url = endpoint;
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

      // 檢查響應類型
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('收到非 JSON 響應:', {
          status: response.status,
          contentType: contentType,
          responseText: text
        });
        throw new Error(`服務器返回了非 JSON 響應 (${response.status}): ${text.substring(0, 100)}...`);
      }

      const data = await response.json();
      console.log('響應數據:', data);

      if (!response.ok) {
        throw new Error(data.message || `掃描失敗 (${response.status})`);
      }

      if (!data.result) {
        console.warn('響應中缺少 result 字段:', data);
      }

      setStatus('掃描完成');
      setResult(data.result || data);
      
      return data;
    } catch (error) {
      console.error('掃描錯誤:', {
        message: error.message,
        stack: error.stack,
        type: error.name
      });
      setError(error.message);
      setStatus('掃描失敗');
      throw error;
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
    setError,
    setIsScanning
  };
};

export default useScan; 