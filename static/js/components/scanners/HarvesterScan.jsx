import React, { useState } from 'react';
import ScanComponent from '../common/ScanComponent';
import HarvesterResult from './HarvesterResult';
import useScan from '../../hooks/useScan';

const HarvesterScan = ({ userId, targetId }) => {
    const [limit, setLimit] = useState(100000);
    const [sources, setSources] = useState('all');
    const scanEndpoint = (userId, targetId) => `/api/harvester/scan/${userId}/${targetId}`;
    
    const {
        isScanning,
        status,
        error,
        startScan
    } = useScan(scanEndpoint);

    const handleScanClick = async () => {
        try {
            await startScan(userId, targetId, {
                body: {
                    limit,
                    sources
                }
            });
        } catch (error) {
            console.error('theHarvester 扫描错误:', error);
        }
    };

    return (
        <div className="scan-section">
            <div className="scan-options">
                <div className="option-group">
                    <label>
                        结果限制:
                        <input
                            type="number"
                            value={limit}
                            onChange={(e) => setLimit(parseInt(e.target.value) || 100000)}
                            min="1"
                            max="100000"
                        />
                    </label>
                </div>
                <div className="option-group">
                    <label>
                        数据源:
                        <select value={sources} onChange={(e) => setSources(e.target.value)}>
                            <option value="all">所有源</option>
                            <option value="baidu">百度</option>
                            <option value="bing">必应</option>
                            <option value="google">谷歌</option>
                            <option value="yahoo">雅虎</option>
                        </select>
                    </label>
                </div>
            </div>

            <ScanComponent
                title="theHarvester"
                isScanning={isScanning}
                status={status}
                error={error}
                onScanClick={handleScanClick}
                renderResult={null}
            />

            <HarvesterResult userId={userId} targetId={targetId} />
        </div>
    );
};

export default HarvesterScan; 