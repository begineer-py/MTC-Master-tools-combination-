import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, Typography, Box, Grid, Chip, LinearProgress, Alert, Button, Dialog, DialogTitle, DialogContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Tooltip, IconButton } from '@mui/material';
import { Refresh, History, Security, Computer, NetworkCheck, Speed, Error as ErrorIcon, CheckCircle, Schedule } from '@mui/icons-material';

const NmapDashboard = ({ targetId }) => {
    const [scanStatus, setScanStatus] = useState('not_started');
    const [scanResult, setScanResult] = useState(null);
    const [scanHistory, setScanHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedScanType, setSelectedScanType] = useState('common');
    const [showHistory, setShowHistory] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(false);

    // 獲取掃描狀態
    const fetchScanStatus = useCallback(async () => {
        try {
            const response = await fetch(`/api/nmap/status/${targetId}?scan_type=${selectedScanType}`);
            const data = await response.json();
            
            if (data.success) {
                setScanStatus(data.status);
                
                // 如果掃描完成，獲取結果
                if (data.status === 'completed') {
                    await fetchScanResult();
                    setAutoRefresh(false);
                }
            }
        } catch (err) {
            console.error('獲取掃描狀態錯誤:', err);
        }
    }, [targetId, selectedScanType]);

    // 獲取掃描結果
    const fetchScanResult = useCallback(async () => {
        try {
            const response = await fetch(`/api/nmap/result/${targetId}?scan_type=${selectedScanType}`);
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    setScanResult(data.result);
                    setError(null);
                }
            } else if (response.status === 404) {
                setScanResult(null);
            }
        } catch (err) {
            console.error('獲取掃描結果錯誤:', err);
            setError('獲取掃描結果失敗');
        }
    }, [targetId, selectedScanType]);

    // 獲取掃描歷史
    const fetchScanHistory = useCallback(async () => {
        try {
            const response = await fetch(`/api/nmap/history/${targetId}`);
            const data = await response.json();
            
            if (data.success) {
                setScanHistory(data.history);
            }
        } catch (err) {
            console.error('獲取掃描歷史錯誤:', err);
        }
    }, [targetId]);

    // 開始掃描
    const startScan = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`/api/nmap/scan/${targetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ scan_type: selectedScanType }),
            });
            
            const data = await response.json();
            
            if (data.success) {
                setScanStatus('scanning');
                setAutoRefresh(true);
                setScanResult(null);
            } else {
                setError(data.message);
            }
        } catch (err) {
            setError('啟動掃描失敗');
        } finally {
            setLoading(false);
        }
    };

    // 自動刷新效果
    useEffect(() => {
        let interval;
        if (autoRefresh && scanStatus === 'scanning') {
            interval = setInterval(fetchScanStatus, 3000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [autoRefresh, scanStatus, fetchScanStatus]);

    // 初始化加載
    useEffect(() => {
        fetchScanStatus();
        fetchScanResult();
        fetchScanHistory();
    }, [fetchScanStatus, fetchScanResult, fetchScanHistory]);

    // 狀態圖標和顏色
    const getStatusConfig = (status) => {
        switch (status) {
            case 'scanning':
                return { icon: <Schedule />, color: 'warning', text: '掃描中' };
            case 'completed':
                return { icon: <CheckCircle />, color: 'success', text: '已完成' };
            case 'not_started':
                return { icon: <Schedule />, color: 'default', text: '未開始' };
            default:
                return { icon: <ErrorIcon />, color: 'error', text: '錯誤' };
        }
    };

    const statusConfig = getStatusConfig(scanStatus);

    // 端口狀態顏色
    const getPortStateColor = (state) => {
        switch (state) {
            case 'open': return 'success';
            case 'filtered': return 'warning';
            case 'closed': return 'error';
            default: return 'default';
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* 控制面板 */}
            <Card sx={{ mb: 3 }}>
                <CardHeader
                    title={
                        <Box display="flex" alignItems="center" gap={2}>
                            <NetworkCheck color="primary" />
                            <Typography variant="h5">Nmap 端口掃描</Typography>
                        </Box>
                    }
                    action={
                        <Box display="flex" gap={1}>
                            <Button
                                variant="outlined"
                                startIcon={<History />}
                                onClick={() => setShowHistory(true)}
                            >
                                歷史記錄
                            </Button>
                            <Button
                                variant="outlined"
                                startIcon={<Refresh />}
                                onClick={fetchScanStatus}
                            >
                                刷新
                            </Button>
                        </Box>
                    }
                />
                <CardContent>
                    <Grid container spacing={3} alignItems="center">
                        <Grid item xs={12} md={4}>
                            <Box display="flex" alignItems="center" gap={2}>
                                <Typography variant="body1">掃描類型:</Typography>
                                <Box display="flex" gap={1}>
                                    <Chip
                                        label="常用端口"
                                        color={selectedScanType === 'common' ? 'primary' : 'default'}
                                        onClick={() => setSelectedScanType('common')}
                                        disabled={scanStatus === 'scanning'}
                                    />
                                    <Chip
                                        label="完整掃描"
                                        color={selectedScanType === 'full' ? 'primary' : 'default'}
                                        onClick={() => setSelectedScanType('full')}
                                        disabled={scanStatus === 'scanning'}
                                    />
                                </Box>
                            </Box>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Box display="flex" alignItems="center" gap={2}>
                                <Typography variant="body1">狀態:</Typography>
                                <Chip
                                    icon={statusConfig.icon}
                                    label={statusConfig.text}
                                    color={statusConfig.color}
                                />
                            </Box>
                        </Grid>
                        <Grid item xs={12} md={4}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={startScan}
                                disabled={loading || scanStatus === 'scanning'}
                                startIcon={<Security />}
                                fullWidth
                            >
                                {scanStatus === 'scanning' ? '掃描中...' : '開始掃描'}
                            </Button>
                        </Grid>
                    </Grid>

                    {scanStatus === 'scanning' && (
                        <Box sx={{ mt: 2 }}>
                            <LinearProgress />
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                預計時間: {selectedScanType === 'common' ? '30-120秒' : '2-5分鐘'}
                            </Typography>
                        </Box>
                    )}

                    {error && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                            {error}
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {/* 掃描結果 */}
            {scanResult && (
                <Grid container spacing={3}>
                    {/* 主機信息 */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardHeader
                                title={
                                    <Box display="flex" alignItems="center" gap={1}>
                                        <Computer />
                                        <Typography variant="h6">主機信息</Typography>
                                    </Box>
                                }
                            />
                            <CardContent>
                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <Typography variant="body2" color="text.secondary">
                                            主機狀態
                                        </Typography>
                                        <Chip
                                            label={scanResult.host_status}
                                            color={scanResult.host_status === 'up' ? 'success' : 'error'}
                                            size="small"
                                        />
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="body2" color="text.secondary">
                                            掃描時間
                                        </Typography>
                                        <Typography variant="body2">
                                            {scanResult.scan_time}
                                        </Typography>
                                    </Grid>
                                    {scanResult.os_info && (
                                        <Grid item xs={12}>
                                            <Typography variant="body2" color="text.secondary">
                                                操作系統
                                            </Typography>
                                            <Typography variant="body2">
                                                {scanResult.os_info.name} (準確度: {scanResult.os_info.accuracy}%)
                                            </Typography>
                                        </Grid>
                                    )}
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* 端口統計 */}
                    <Grid item xs={12} md={6}>
                        <Card>
                            <CardHeader
                                title={
                                    <Box display="flex" alignItems="center" gap={1}>
                                        <Speed />
                                        <Typography variant="h6">端口統計</Typography>
                                    </Box>
                                }
                            />
                            <CardContent>
                                {scanResult.port_statistics && (
                                    <Grid container spacing={2}>
                                        <Grid item xs={6}>
                                            <Typography variant="h4" color="success.main">
                                                {scanResult.port_statistics.open}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                開放端口
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={6}>
                                            <Typography variant="h4" color="warning.main">
                                                {scanResult.port_statistics.filtered}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                過濾端口
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={6}>
                                            <Typography variant="h4" color="error.main">
                                                {scanResult.port_statistics.closed}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                關閉端口
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={6}>
                                            <Typography variant="h4" color="text.primary">
                                                {scanResult.port_statistics.total}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                總端口數
                                            </Typography>
                                        </Grid>
                                    </Grid>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* 端口詳情 */}
                    <Grid item xs={12}>
                        <Card>
                            <CardHeader
                                title={
                                    <Typography variant="h6">端口詳情</Typography>
                                }
                            />
                            <CardContent>
                                <TableContainer component={Paper} variant="outlined">
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>端口</TableCell>
                                                <TableCell>狀態</TableCell>
                                                <TableCell>服務</TableCell>
                                                <TableCell>版本</TableCell>
                                                <TableCell>協議</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {scanResult.ports && scanResult.ports.map((port, index) => (
                                                <TableRow key={index}>
                                                    <TableCell>
                                                        <Typography variant="body2" fontWeight="bold">
                                                            {port.port}
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={port.state}
                                                            color={getPortStateColor(port.state)}
                                                            size="small"
                                                        />
                                                    </TableCell>
                                                    <TableCell>{port.service || '未知'}</TableCell>
                                                    <TableCell>{port.version || '-'}</TableCell>
                                                    <TableCell>{port.protocol || 'tcp'}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            )}

            {/* 歷史記錄對話框 */}
            <Dialog open={showHistory} onClose={() => setShowHistory(false)} maxWidth="md" fullWidth>
                <DialogTitle>掃描歷史記錄</DialogTitle>
                <DialogContent>
                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>掃描時間</TableCell>
                                    <TableCell>掃描類型</TableCell>
                                    <TableCell>主機狀態</TableCell>
                                    <TableCell>總端口數</TableCell>
                                    <TableCell>開放端口</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {scanHistory.map((record, index) => (
                                    <TableRow key={index}>
                                        <TableCell>{record.scan_time}</TableCell>
                                        <TableCell>
                                            <Chip
                                                label={record.scan_type === 'common' ? '常用端口' : '完整掃描'}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={record.host_status}
                                                color={record.host_status === 'up' ? 'success' : 'error'}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>{record.port_count}</TableCell>
                                        <TableCell>
                                            <Typography variant="body2" color="success.main" fontWeight="bold">
                                                {record.open_ports}
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </DialogContent>
            </Dialog>
        </Box>
    );
};

export default NmapDashboard; 