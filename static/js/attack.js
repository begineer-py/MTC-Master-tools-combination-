import React from 'react';
import { createRoot } from 'react-dom/client';
import Attack from './components/Attack';
import ErrorBoundary from './components/common/ErrorBoundary';

// 獲取初始數據
const initialData = window.INITIAL_DATA || {};

// 驗證初始數據
if (!initialData.targetId || !initialData.currentUser?.id) {
  console.error('缺少必要的初始數據:', initialData);
}

// 創建根元素
const container = document.getElementById('attack-root');
if (!container) {
  console.error('找不到根元素 #attack-root');
}

const root = createRoot(container);

// 渲染 React 組件
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <Attack 
        targetId={initialData.targetId}
        target={initialData.target || {}}
        currentUser={initialData.currentUser || {}}
      />
    </ErrorBoundary>
  </React.StrictMode>
); 