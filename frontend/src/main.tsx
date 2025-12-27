// 檔案路徑: frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';

// 操！這裡！導入你的 App 元件，而不是什麼 IndexPage！
// App.tsx 才是你整個應用程式的根！
import App from './App.tsx'; 

// 導入你的全域 CSS

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* 這裡渲染 App 元件！App 會自己處理要顯示哪個頁面！ */}
    <App />
  </React.StrictMode>,
);
