import React from 'react';
import NmapScan from './scanners/NmapScan';
import CrtshScan from './scanners/CrtshScan';
import WebtechScan from './scanners/WebtechScan';
import HarvesterScan from './scanners/HarvesterScan';
import FlareSolverr from './scanners/FlareSolverr';

const Attack = ({ targetId, target = {}, currentUser = {} }) => {
  // 添加数据验证
  if (!targetId || !currentUser.id) {
    return (
      <div className="error-message">
        <h4>加载错误</h4>
        <p>无法加载扫描页面：缺少必要的目标或用户信息</p>
        <p>请确保您已正确登录并选择了扫描目标</p>
      </div>
    );
  }

  return (
    <div className="container">
      <h2>扫描页面</h2>
      
      <div className="scan-navigation">
        <a href={`/attack/vulnerability/${currentUser.id}/${targetId}`} 
           className="vulnerability-button">
          进入漏洞扫描页面
        </a>
      </div>

      <div className="target-info">
        <h3>目标信息</h3>
        <p>目标 ID: {targetId}</p>
        <p>目标 IP: {target.target_ip || '未设置'}</p>
        <p>目标端口: {target.target_port || '未设置'}</p>
        <p>目标用户名: {target.target_username || '未设置'}</p>
        <p>目标密码: {target.target_password || '未设置'}</p>
      </div>

      <div className="scan-controls">
        <h3>基础扫描</h3>
        
        <NmapScan 
          userId={currentUser.id}
          targetId={targetId}
        />

        <CrtshScan 
          userId={currentUser.id}
          targetId={targetId}
        />

        <WebtechScan 
          userId={currentUser.id}
          targetId={targetId}
        />

        <HarvesterScan 
          userId={currentUser.id}
          targetId={targetId}
        />

        <FlareSolverr 
          userId={currentUser.id}
          targetId={targetId}
        />
      </div>
    </div>
  );
};

export default Attack; 