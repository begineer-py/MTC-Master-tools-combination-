import React, { useState, useEffect } from 'react';

const NmapResult = ({ targetId }) => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchResults = async () => {
        try {
            const response = await fetch(`/api/nmap/result/${targetId}`);
            console.log('Nmap結果響應狀態:', response.status);
            
            if (!response.ok) {
                if (response.status === 404) {
                    console.log('掃描結果尚未就緒');
                    return null;
                }
                throw new Error(`獲取結果失敗 (${response.status})`);
            }

            const data = await response.json();
            console.log('Nmap原始結果數據:', data);

            if (!data.success) {
                throw new Error(data.message || '獲取結果失敗');
            }

            // 处理和转换数据格式
            const processedResult = {
                scan_type: data.result.scan_type || 'common',
                host_status: data.result.host_status || 'unknown',
                ports: Array.isArray(data.result.ports) ? data.result.ports : [],
                os_info: data.result.os_info || null,
                error: data.result.error || null
            };

            console.log('處理後的結果數據:', processedResult);
            return processedResult;
        } catch (err) {
            console.error('獲取Nmap結果錯誤:', err);
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

    // 格式化端口信息
    const formatPorts = (ports) => {
        if (!Array.isArray(ports) || ports.length === 0) {
            return (
                <div className="alert alert-warning">
                    <i className="fas fa-info-circle me-2"></i>
                    未發現開放端口
                </div>
            );
        }

        // 按端口号排序
        const sortedPorts = [...ports].sort((a, b) => parseInt(a.port) - parseInt(b.port));

        return (
            <div className="table-responsive">
                <table className="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>端口</th>
                            <th>狀態</th>
                            <th>服務</th>
                            <th>版本</th>
                            <th>協議</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedPorts.map((port, index) => (
                            <tr key={index} className={port.state === 'open' ? 'table-success' : ''}>
                                <td>
                                    <span className="badge bg-primary">
                                        {port.port}
                                    </span>
                                </td>
                                <td>
                                    <span className={`badge ${port.state === 'open' ? 'bg-success' : 'bg-danger'}`}>
                                        {port.state === 'open' ? '開放' : '關閉'}
                                    </span>
                                </td>
                                <td>{port.service || '未知'}</td>
                                <td>
                                    {port.version ? (
                                        <span className="badge bg-info">
                                            {port.version}
                                        </span>
                                    ) : '未知'}
                                </td>
                                <td>
                                    <span className="badge bg-secondary">
                                        {port.protocol || 'tcp'}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    // 格式化操作系统信息
    const formatOsInfo = (osInfo) => {
        if (!osInfo) return null;

        return (
            <div className="os-info mb-3">
                <h6 className="mb-2">
                    <i className="fas fa-desktop me-2"></i>
                    操作系統信息
                </h6>
                <div className="card bg-light">
                    <div className="card-body">
                        <div className="row">
                            <div className="col-md-6">
                                <strong>名稱：</strong> {osInfo.name || '未知'}
                            </div>
                            {osInfo.accuracy && (
                                <div className="col-md-6">
                                    <strong>準確度：</strong>
                                    <div className="progress" style={{ height: '20px' }}>
                                        <div
                                            className="progress-bar bg-success"
                                            role="progressbar"
                                            style={{ width: `${osInfo.accuracy}%` }}
                                            aria-valuenow={osInfo.accuracy}
                                            aria-valuemin="0"
                                            aria-valuemax="100"
                                        >
                                            {osInfo.accuracy}%
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                        {osInfo.details && (
                            <div className="mt-3">
                                <strong>詳細信息：</strong>
                                <ul className="list-group mt-2">
                                    {Object.entries(osInfo.details).map(([key, value]) => (
                                        <li key={key} className="list-group-item d-flex justify-content-between align-items-center">
                                            {key}
                                            <span className="badge bg-primary rounded-pill">{value}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="nmap-result mt-3">
            <div className="card">
                <div className="card-header bg-primary text-white">
                    <h5 className="card-title mb-0">
                        <i className="fas fa-network-wired me-2"></i>
                        Nmap 掃描結果
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
                            <div className="row mb-3">
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <strong>
                                            <i className="fas fa-search me-2"></i>
                                            掃描類型：
                                        </strong>
                                        <span className="badge bg-secondary ms-2">
                                            {result.scan_type === 'full' ? '完整掃描' : '常用端口掃描'}
                                        </span>
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="mb-3">
                                        <strong>
                                            <i className="fas fa-signal me-2"></i>
                                            主機狀態：
                                        </strong>
                                        <span className={`badge ms-2 ${result.host_status === 'up' ? 'bg-success' : 'bg-danger'}`}>
                                            {result.host_status === 'up' ? '在線' : '離線'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="mb-3">
                                <h6 className="mb-2">
                                    <i className="fas fa-plug me-2"></i>
                                    端口掃描結果
                                </h6>
                                {formatPorts(result.ports)}
                            </div>

                            {result.os_info && formatOsInfo(result.os_info)}

                            <div className="mt-3">
                                <a
                                    href={`/api/nmap/file/${targetId}?format=txt`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-sm btn-outline-primary me-2"
                                >
                                    <i className="fas fa-download me-1"></i>
                                    下載 TXT
                                </a>
                                <a
                                    href={`/api/nmap/file/${targetId}?format=xml`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-sm btn-outline-primary me-2"
                                >
                                    <i className="fas fa-file-code me-1"></i>
                                    下載 XML
                                </a>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default NmapResult; 