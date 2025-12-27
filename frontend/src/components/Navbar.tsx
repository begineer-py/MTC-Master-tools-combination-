// 檔案路徑: frontend/src/components/Navbar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom'; // 導入 NavLink
import './Navbar.css'; // 導入專屬的 CSS

function Navbar() {
  return (
    <nav className="main-nav">
      <div className="nav-logo">
        <NavLink to="/">C2 Platform</NavLink>
      </div>
      <div className="nav-links">
        <NavLink to="/" end>目標列表</NavLink>
        {/* 之後你可以加上 <NavLink to="/scans">掃描歷史</NavLink> 等等 */}
      </div>
    </nav>
  );
}

export default Navbar;