import React, { useState, useEffect } from 'react';
import Loading from '../common/Loading';

const CrtshResult = ({ targetId }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchResults = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/crtsh/result/${targetId}`, {
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
                setResult(data.result);
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
    }, [targetId]);

    const renderResult = () => {
        if (!result) return null;

        const filteredDomains = result.domains.filter(domain => 
            domain.toLowerCase().includes(searchTerm.toLowerCase())
        );

        return (
            <div className="crtsh-results">
                <div className="result-header">
                    <h3>CRT.sh 掃描結果</h3>
                    <div className="result-info">
                        <p><strong>掃描時間:</strong> {new Date(result.scan_time * 1000).toLocaleString()}</p>
                        <p><strong>發現域名數量:</strong> {filteredDomains.length}</p>
                        <p><strong>狀態:</strong> {result.status}</p>
                    </div>
                </div>

                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="搜索域名..."
                    className="search-input"
                />

                <div className="domain-list">
                    <table className="tech-table">
                        <thead>
                            <tr>
                                <th>域名</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredDomains.map((domain, index) => (
                                <tr key={index}>
                                    <td className="domain-cell">{domain}</td>
                                    <td>
                                        <button
                                            className="copy-button"
                                            onClick={() => {
                                                navigator.clipboard.writeText(domain);
                                            }}
                                        >
                                            複製
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="result-actions">
                    <button 
                        onClick={fetchResults}
                        className="refresh-button"
                    >
                        刷新結果
                    </button>
                    <button 
                        onClick={() => window.location.href = `/api/crtsh/download/${targetId}`}
                        className="download-button"
                    >
                        下載結果
                    </button>
                </div>
            </div>
        );
    };

    if (loading) {
        return <Loading text="加載 CRT.sh 掃描結果中..." />;
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

export default CrtshResult; 