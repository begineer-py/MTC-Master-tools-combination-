import React, { useState, useEffect, createContext, useContext } from 'react';
import { Snackbar, Alert, AlertTitle, Box, Typography, LinearProgress } from '@mui/material';
import { CheckCircle, Error, Info, Warning } from '@mui/icons-material';

// 創建通知上下文
const NotificationContext = createContext();

// 通知提供者組件
export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);

    const addNotification = (notification) => {
        const id = Date.now() + Math.random();
        const newNotification = {
            id,
            ...notification,
            timestamp: new Date()
        };
        
        setNotifications(prev => [...prev, newNotification]);
        
        // 自動移除通知（除非設置為持久）
        if (!notification.persistent) {
            setTimeout(() => {
                removeNotification(id);
            }, notification.duration || 5000);
        }
        
        return id;
    };

    const removeNotification = (id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    const clearAllNotifications = () => {
        setNotifications([]);
    };

    return (
        <NotificationContext.Provider value={{
            notifications,
            addNotification,
            removeNotification,
            clearAllNotifications
        }}>
            {children}
            <NotificationContainer />
        </NotificationContext.Provider>
    );
};

// 通知容器組件
const NotificationContainer = () => {
    const { notifications, removeNotification } = useContext(NotificationContext);

    return (
        <Box sx={{ position: 'fixed', top: 20, right: 20, zIndex: 9999, maxWidth: 400 }}>
            {notifications.map((notification) => (
                <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClose={() => removeNotification(notification.id)}
                />
            ))}
        </Box>
    );
};

// 單個通知項組件
const NotificationItem = ({ notification, onClose }) => {
    const [open, setOpen] = useState(true);

    const handleClose = () => {
        setOpen(false);
        setTimeout(onClose, 300); // 等待動畫完成
    };

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'success': return <CheckCircle />;
            case 'error': return <Error />;
            case 'warning': return <Warning />;
            case 'info': return <Info />;
            default: return <Info />;
        }
    };

    return (
        <Snackbar
            open={open}
            onClose={handleClose}
            anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            sx={{ position: 'relative', mb: 1 }}
        >
            <Alert
                severity={notification.severity || 'info'}
                onClose={handleClose}
                icon={getSeverityIcon(notification.severity)}
                sx={{ minWidth: 300, maxWidth: 400 }}
            >
                {notification.title && (
                    <AlertTitle>{notification.title}</AlertTitle>
                )}
                <Typography variant="body2">
                    {notification.message}
                </Typography>
                
                {notification.progress !== undefined && (
                    <Box sx={{ mt: 1 }}>
                        <LinearProgress 
                            variant="determinate" 
                            value={notification.progress}
                            sx={{ mb: 1 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                            {notification.progressText || `${notification.progress}% 完成`}
                        </Typography>
                    </Box>
                )}
                
                {notification.details && (
                    <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 1 }}>
                        <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                            {notification.details}
                        </Typography>
                    </Box>
                )}
                
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    {notification.timestamp.toLocaleTimeString()}
                </Typography>
            </Alert>
        </Snackbar>
    );
};

// 使用通知的 Hook
export const useNotification = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotification must be used within a NotificationProvider');
    }
    return context;
};

// 預定義的通知類型
export const NotificationTypes = {
    SCAN_STARTED: (scanType, targetId) => ({
        severity: 'info',
        title: '掃描已開始',
        message: `正在對目標 ${targetId} 執行 ${scanType === 'common' ? '常用端口' : '完整'} 掃描`,
        duration: 3000
    }),
    
    SCAN_PROGRESS: (progress, message) => ({
        severity: 'info',
        title: '掃描進行中',
        message: message || '正在掃描...',
        progress: progress,
        persistent: true
    }),
    
    SCAN_COMPLETED: (results) => ({
        severity: 'success',
        title: '掃描完成',
        message: `發現 ${results.openPorts || 0} 個開放端口`,
        details: results.summary,
        duration: 8000
    }),
    
    SCAN_ERROR: (error) => ({
        severity: 'error',
        title: '掃描失敗',
        message: error.message || '掃描過程中發生錯誤',
        details: error.details,
        duration: 10000
    }),
    
    RESULT_UPDATED: (targetId) => ({
        severity: 'success',
        title: '結果已更新',
        message: `目標 ${targetId} 的掃描結果已更新`,
        duration: 3000
    }),
    
    CONNECTION_ERROR: () => ({
        severity: 'error',
        title: '連接錯誤',
        message: '無法連接到服務器，請檢查網絡連接',
        duration: 5000
    })
};

export default NotificationProvider;
