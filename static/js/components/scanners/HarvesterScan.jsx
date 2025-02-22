import React, { useState } from 'react';
import ScanComponent from '../common/ScanComponent';
import HarvesterResult from './HarvesterResult';
import useScan from '../../hooks/useScan';

const HarvesterScan = ({ userId, targetId }) => {
    const [limit, setLimit] = useState(100000);
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
                    sources: 'all'  // 直接使用所有搜索源
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