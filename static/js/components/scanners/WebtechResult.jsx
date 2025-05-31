import React, { useState, useEffect } from 'react';

const WebtechResult = ({ targetId }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchResults = async () => {
    try {
      const response = await fetch(`/api/webtech/result/${targetId}`);
      console.log('Webtech結果響應狀態:', response.status);
      
      if (!response.ok) {
        if (response.status === 404) {
          console.log('掃描結果尚未就緒');
          return null;
        }
        throw new Error(`獲取結果失敗 (${response.status})`);
      }

      const contentType = response.headers.get('content-type');
      console.log('響應內容類型:', contentType);

      const data = await response.json();
      console.log('Webtech結果數據:', data);

      if (!data.success) {
        throw new Error(data.message || '獲取結果失敗');
      }

      return data.result;
    } catch (err) {
      console.error('獲取Webtech結果錯誤:', err);
      throw err;
    }
  };

  useEffect(() => {
    let intervalId;
    let attempts = 0;
    const maxAttempts = 60; // 最多輪詢5分鐘 (5秒間隔)

    const pollResults = async () => {
      if (attempts >= maxAttempts) {
        setError('掃描超時，請稍後重試');
        setLoading(false);
        clearInterval(intervalId);
        return;
      }

      try {
        const data = await fetchResults();
        attempts++;

        if (data) {
          console.log('獲取到結果:', data);
          setResult(data);
          setLoading(false);
          clearInterval(intervalId);
        } else {
          console.log(`等待結果中... (嘗試 ${attempts}/${maxAttempts})`);
        }
      } catch (err) {
        console.error('輪詢錯誤:', err);
        setError(err.message);
        setLoading(false);
        clearInterval(intervalId);
      }
    };

    // 立即執行一次
    pollResults();
    // 每5秒輪詢一次
    intervalId = setInterval(pollResults, 5000);

    return () => {
      console.log('清理輪詢定時器');
      clearInterval(intervalId);
    };
  }, [targetId]);

  if (loading) {
    return (
      <div className="alert alert-info">
        <div className="spinner-border spinner-border-sm me-2" role="status">
          <span className="visually-hidden">加載中...</span>
        </div>
        正在獲取掃描結果...
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        <i className="fas fa-exclamation-circle me-2"></i>
        {error}
      </div>
    );
  }

  if (!result) {
    return null;
  }

  // 格式化技術信息
  const formatTechnologies = (technologies) => {
    if (!technologies || Object.keys(technologies).length === 0) {
      return <div>未檢測到技術信息</div>;
    }

    return Object.entries(technologies).map(([category, techs]) => (
      <div key={category} className="mb-4">
        <h5 className="mb-3">{category}</h5>
        <div className="table-responsive">
          <table className="table table-striped table-hover">
            <thead>
              <tr>
                <th>技術名稱</th>
                <th>版本</th>
                <th>置信度</th>
              </tr>
            </thead>
            <tbody>
              {techs.map((tech, index) => (
                <tr key={index}>
                  <td>{tech.name}</td>
                  <td>{tech.version || '未知'}</td>
                  <td>
                    <div className="progress" style={{ height: '20px' }}>
                      <div
                        className="progress-bar bg-success"
                        role="progressbar"
                        style={{ width: `${tech.confidence}%` }}
                        aria-valuenow={tech.confidence}
                        aria-valuemin="0"
                        aria-valuemax="100"
                      >
                        {tech.confidence}%
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    ));
  };

  return (
    <div className="webtech-result mt-3">
      <div className="card">
        <div className="card-header bg-primary text-white">
          <h5 className="card-title mb-0">
            <i className="fas fa-code me-2"></i>
            Web技術掃描結果
          </h5>
        </div>
        <div className="card-body">
          {result.error ? (
            <div className="alert alert-danger">
              <i className="fas fa-exclamation-circle me-2"></i>
              {result.error}
            </div>
          ) : (
            <>
              <div className="mb-3">
                <strong>目標網站：</strong> {result.target_url}
              </div>
              <div className="mb-3">
                <strong>掃描時間：</strong> {result.scan_time}
              </div>
              <div className="mb-3">
                <strong>檢測到的技術：</strong>
                {formatTechnologies(result.technologies)}
              </div>
              <div className="mt-3">
                <button
                  className="btn btn-sm btn-outline-primary me-2"
                  onClick={() => window.location.href = `/api/webtech/file/${targetId}?format=txt`}
                >
                  <i className="fas fa-download me-1"></i>
                  下載 TXT
                </button>
                <button
                  className="btn btn-sm btn-outline-primary me-2"
                  onClick={() => window.location.href = `/api/webtech/file/${targetId}?format=csv`}
                >
                  <i className="fas fa-file-csv me-1"></i>
                  下載 CSV
                </button>
                <button
                  className="btn btn-sm btn-outline-primary"
                  onClick={() => window.location.href = `/api/webtech/file/${targetId}?format=json`}
                >
                  <i className="fas fa-file-code me-1"></i>
                  下載 JSON
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebtechResult; 