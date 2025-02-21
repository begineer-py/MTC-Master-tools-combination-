import React, { useState, useEffect } from 'react';
import Loading from '../common/Loading';

const ParamSpiderResult = ({ userId, targetId }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const fetchResults = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/paramspider/result/${userId}/${targetId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || '獲取掃描結果失敗');
            }

            if (data.status === 'success') {
                setResult(data.data);
            } else if (response.status === 302) {
                // 如果正在掃描中，設置定時器重新獲取結果
                setTimeout(fetchResults, 5000);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchResults();
    }, [userId, targetId]);

    const renderResult = () => {
        if (!result) return null;

        return (
            <div className="paramspider-results">
                <div className="result-header">
                    <h3>ParamSpider 掃描結果</h3>
                    <div className="result-info">
                        <p><strong>總 URL 數:</strong> {result.total_urls}</p>
                        <p><strong>唯一參數數:</strong> {result.unique_parameters}</p>
                        <p><strong>掃描時間:</strong> {result.created_at}</p>
                        <p><strong>狀態:</strong> {result.status}</p>
                    </div>
                </div>

                {result.result_text && (
                    <div className="result-content">
                        <h4>發現的 URL:</h4>
                        <pre className="result-text">{result.result_text}</pre>
                    </div>
                )}

                {result.error_message && (
                    <div className="error-details">
                        <h4>錯誤信息:</h4>
                        <p>{result.error_message}</p>
                    </div>
                )}

                <div className="result-actions">
                    <button 
                        onClick={fetchResults}
                        className="refresh-button"
                    >
                        刷新結果
                    </button>
                    {result.result_text && (
                        <>
                            <button 
                                onClick={() => navigator.clipboard.writeText(result.result_text)}
                                className="copy-button"
                            >
                                複製結果
                            </button>
                            <button 
                                onClick={() => window.location.href = `/api/paramspider/download/${userId}/${targetId}`}
                                className="download-button"
                            >
                                下載結果
                            </button>
                        </>
                    )}
                </div>
            </div>
        );
    };

    if (loading) {
        return <Loading text="加載 ParamSpider 掃描結果中..." />;
    }

    if (error) {
        return (
            <div className="error-message">
                <h4>錯誤</h4>
                <p>{error}</p>
                <button onClick={fetchResults} className="retry-button">
                    重試
                </button>
            </div>
        );
    }

    return renderResult();
};

export default ParamSpiderResult; 