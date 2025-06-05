import React from 'react';
import NmapScan from './scanners/NmapScan';
import CrtshScan from './scanners/CrtshScan';
import WebtechScan from './scanners/WebtechScan';
import FlareSolverr from './scanners/FlareSolverr';
import LinksFinderScan from './scanners/LinksFinderScan';
import GauScan from './scanners/GauScan';

const Attack = ({ targetId, target = {} }) => {
  // 在檢查前立即記錄 props 的狀態
  console.log('Attack Component Render - Props Check:', {
      targetIdValue: targetId,
      targetValue: target,
      targetIdIsTruthy: !!targetId, // 檢查 targetId 是否為真值
      targetIsTruthy: !!target    // 檢查 target 是否為真值
  });

  // 验证必要的数据
  if (!targetId || !target) {
    // 如果條件判斷失敗 (即進入此 if 塊)，再次記錄狀態
    console.error('Condition Failed! Logging values inside if block:', {
        targetIdValue: targetId,
        targetValue: target,
        targetIdIsTruthy: !!targetId,
        targetIsTruthy: !!target
    });
    console.error('缺少必要的初始數據:', { targetId, target }); // 保留原始錯誤日誌
    return (
      <div className="alert alert-danger">
        <h4>加載錯誤</h4>
        <p>無法加載掃描頁面：缺少目標信息</p>
        <p>請確保已選擇了掃描目標</p>
      </div>
    );
  }

  // 验证目标数据的完整性 (如果第一個 if 通過，會執行到這裡)
  if (!target.domain || !target.target_ip || !target.target_port) {
    console.error('目標數據不完整:', target);
    return (
      <div className="alert alert-danger">
        <h4>目標數據不完整</h4>
        <p>請確保目標包含以下信息：</p>
        <ul>
          <li>域名 (domain)</li>
          <li>目標URL (target_ip)</li>
          <li>端口 (target_port)</li>
        </ul>
      </div>
    );
  }

  return (
    <div className="container">
      <h2>掃描頁面</h2>
      
      <div className="scan-navigation mb-4">
        <div className="row">
          <div className="col-md-3 mb-2">
        <a href={`/attack/vulnerability/${targetId}`} 
               className="btn btn-warning w-100">
          <i className="fas fa-bug me-2"></i>
          進入漏洞掃描頁面
        </a>
          </div>
          <div className="col-md-3 mb-2">
            <a href={`/api/nmap/dashboard?target_id=${targetId}`} 
               className="btn btn-primary w-100"
               target="_blank"
               rel="noopener noreferrer">
              <i className="fas fa-network-wired me-2"></i>
              進入 Nmap 掃描器界面
            </a>
          </div>
          <div className="col-md-3 mb-2">
            <a href={`/api/crtsh/dashboard?target_id=${targetId}`} 
               className="btn btn-success w-100"
               target="_blank"
               rel="noopener noreferrer">
              <i className="fas fa-search me-2"></i>
              進入 crt.sh 掃描器界面
            </a>
          </div>
          <div className="col-md-3 mb-2">
            <a href={`/api/gau/dashboard?target_id=${targetId}`} 
               className="btn btn-info w-100"
               target="_blank"
               rel="noopener noreferrer"
               style={{backgroundColor: '#FF9800', borderColor: '#FF9800'}}>
              <i className="fas fa-link me-2"></i>
              進入 Gau URL 掃描器界面
            </a>
          </div>
        </div>
      </div>

      <div className="target-info card mb-4">
        <div className="card-header bg-info text-white">
          <h3 className="card-title mb-0">
            <i className="fas fa-info-circle me-2"></i>
            目標信息
          </h3>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-3">
              <strong>目標 ID:</strong> {targetId}
            </div>
            <div className="col-md-3">
              <strong>目標 URL:</strong> 
              <a href={target.target_ip} target="_blank" rel="noopener noreferrer">
                {target.target_ip}
              </a>
            </div>
            <div className="col-md-3">
              <strong>目標域名:</strong> {target.domain}
            </div>
            <div className="col-md-3">
              <strong>目標端口:</strong> {target.target_port}
            </div>
          </div>
        </div>
      </div>

      <div className="alert alert-info">
        <h4>
          <i className="fas fa-info-circle me-2"></i>
          掃描工具說明
        </h4>
        <p>請使用上方的導航按鈕進入相應的掃描界面：</p>
        <ul>
          <li><strong>漏洞掃描頁面</strong>：進行目標的漏洞檢測和安全評估</li>
          <li><strong>Nmap 掃描器界面</strong>：進行網絡掃描、端口檢測和服務識別</li>
          <li><strong>crt.sh 掃描器界面</strong>：進行子域名發現和證書透明度日誌查詢</li>
          <li><strong>Gau URL 掃描器界面</strong>：從多個來源收集目標的 URL 列表（Wayback Machine、Common Crawl 等）</li>
        </ul>
        <p className="mb-0">
          <i className="fas fa-lightbulb me-1"></i>
          <small>目標 ID ({targetId}) 將自動傳遞到掃描器界面</small>
        </p>
      </div>
    </div>
  );
};

export default Attack; 