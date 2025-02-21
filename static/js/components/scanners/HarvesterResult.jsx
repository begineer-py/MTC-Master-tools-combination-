import React, { useState, useEffect } from 'react';
import Loading from '../common/Loading';

const HarvesterResult = ({ userId, targetId }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchResults = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/harvester/result/${userId}/${targetId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || '获取扫描结果失败');
            }

            if (data.status === 'success') {
                setResult(data.data);
            } else if (response.status === 302) {
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

    const renderSection = (title, items, type = 'list') => {
        if (!items || items.length === 0) return null;

        const filteredItems = items.filter(item => 
            JSON.stringify(item).toLowerCase().includes(searchTerm.toLowerCase())
        );

        return (
            <div className="section">
                <h4>{title}</h4>
                {type === 'list' ? (
                    <ul>
                        {filteredItems.map((item, index) => (
                            <li key={index}>
                                {typeof item === 'string' ? item : JSON.stringify(item)}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <pre>{JSON.stringify(filteredItems, null, 2)}</pre>
                )}
            </div>
        );
    };

    const renderResult = () => {
        if (!result) return null;

        return (
            <div className="harvester-results">
                <div className="result-header">
                    <h3>theHarvester 扫描结果</h3>
                    <div className="result-info">
                        <p><strong>扫描时间:</strong> {result.scan_time}</p>
                        <p><strong>状态:</strong> {result.status}</p>
                        <p><strong>数据源:</strong> {result.scan_sources}</p>
                    </div>
                </div>

                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="搜索结果..."
                    className="search-input"
                />

                {renderSection('发现的 URL', result.urls)}
                {renderSection('电子邮件', result.emails)}
                {renderSection('主机', result.hosts)}
                {renderSection('子域名', result.subdomains)}
                {renderSection('端口', result.ports)}
                {renderSection('人员信息', result.people)}
                {renderSection('社交媒体', result.social_media)}
                {renderSection('DNS 记录', result.dns_records)}
                {renderSection('搜索引擎结果', result.search_results, 'json')}

                {result.error && (
                    <div className="error-details">
                        <h4>错误信息</h4>
                        <p>{result.error}</p>
                    </div>
                )}

                <div className="result-actions">
                    <button 
                        onClick={fetchResults}
                        className="refresh-button"
                    >
                        刷新结果
                    </button>
                    <button 
                        onClick={() => window.location.href = `/api/harvester/download/${userId}/${targetId}`}
                        className="download-button"
                    >
                        下载结果
                    </button>
                </div>
            </div>
        );
    };

    if (loading) {
        return <Loading text="加载 theHarvester 扫描结果中..." />;
    }

    if (error) {
        return (
            <div className="error-message">
                <h4>错误</h4>
                <p>{error}</p>
                <button onClick={fetchResults} className="retry-button">
                    重试
                </button>
            </div>
        );
    }

    return renderResult();
};

export default HarvesterResult; 