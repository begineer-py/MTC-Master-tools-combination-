import React from 'react';
import { createRoot } from 'react-dom/client';
import GauResult from '../components/scanners/GauResult';

// 获取初始数据
const { userId, targetId } = window.INITIAL_DATA || {};

// 渲染组件
const container = document.getElementById('gau-result-root');
if (container) {
  const root = createRoot(container);
  root.render(
    <GauResult userId={userId} targetId={targetId} />
  );
} 