import React, { useState, useEffect } from 'react';
import Loading from '../common/Loading';
import { formatNmapResults } from '../../utils/formatResults';

const NmapResult = ({ userId, targetId }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const fetchResults = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/nmap/result/${userId}/${targetId}`, {
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
                setResult(formatNmapResults(data.data));
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

    const renderPortDetails = (ports) => (
        <div className="port-details">
            <h4>端口詳情</h4>
            <table className="tech-table">
                <thead>
                    <tr>
                        <th>端口</th>
                        <th>狀態</th>
                        <th>服務</th>
                        <th>產品</th>
                        <th>版本</th>
                    </tr>
                </thead>
                <tbody>
                    {Object.entries(ports).map(([port, info]) => (
                        <tr key={port} className={info.state}>
                            <td>{port}</td>
                            <td>{info.state}</td>
                            <td>{info.name || '未知'}</td>
                            <td>{info.product || '未知'}</td>
                            <td>{info.version || '未知'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    const renderResult = () => {
        if (!result) return null;

        return (
            <div className="nmap-results">
                <div className="result-header">
                    <h3>Nmap 掃描結果</h3>
                    <div className="result-info">
                        <p><strong>目標主機:</strong> {result.host}</p>
                        <p><strong>主機名:</strong> {result.hostname}</p>
                        <p><strong>狀態:</strong> {result.state}</p>
                        <p><strong>掃描時間:</strong> {result.scan_time}</p>
                    </div>
                </div>

                <div className="port-statistics">
                    <h4>端口統計</h4>
                    <ul>
                        <li>開放端口: {result.portStats.open}</li>
                        <li>過濾端口: {result.portStats.filtered}</li>
                        <li>關閉端口: {result.portStats.closed}</li>
                    </ul>
                </div>

                {renderPortDetails(result.ports)}

                <div className="result-actions">
                    <button 
                        onClick={fetchResults}
                        className="refresh-button"
                    >
                        刷新結果
                    </button>
                </div>
            </div>
        );
    };

    if (loading) {
        return <Loading text="加載掃描結果中..." />;
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

export default NmapResult; 