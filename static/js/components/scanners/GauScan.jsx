import React, { useState } from 'react';

const GauScan = ({ userId, targetId }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [options, setOptions] = useState({
    threads: 30,
    verbose: false,
    providers: "wayback,commoncrawl,otx,urlscan",
    blacklist: "ttf,woff,svg,png,jpg,gif,jpeg,ico"
  });

  const handleOptionChange = (e) => {
    const { name, value, type, checked } = e.target;
    setOptions({
      ...options,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const startScan = async () => {
    try {
      setIsScanning(true);
      console.log(`开始Gau扫描，目标ID: ${targetId}`);
      
      const response = await fetch(`/api/gau/scan/${userId}/${targetId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options)
      });
      
      const data = await response.json();
      
      if (data.success) {
        alert('Gau扫描已启动，结果将实时更新。请点击"查看扫描结果"按钮查看进度。');
        console.log('扫描已启动:', data);
      } else {
        alert(`启动扫描失败: ${data.message}`);
        console.error('启动扫描失败:', data.message);
      }
    } catch (error) {
      alert(`启动扫描时出错: ${error.message}`);
      console.error('启动扫描时出错:', error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="scan-component">
      <h4>Gau URL 扫描</h4>
      <p>使用Gau工具从多个来源（Wayback Machine、Common Crawl等）获取目标的URL列表</p>
      
      <div className="scan-options">
        <div className="option-group">
          <label>
            线程数:
            <input
              type="number"
              name="threads"
              value={options.threads}
              onChange={handleOptionChange}
              min="1"
              max="100"
            />
          </label>
          <small className="text-muted">提示：增加线程数可以提高扫描速度，建议值：30-50</small>
        </div>
        
        <div className="option-group">
          <label>
            数据提供者:
            <input
              type="text"
              name="providers"
              value={options.providers}
              onChange={handleOptionChange}
              placeholder="wayback,commoncrawl,otx,urlscan"
            />
          </label>
        </div>
        
        <div className="option-group">
          <label>
            排除文件类型:
            <input
              type="text"
              name="blacklist"
              value={options.blacklist}
              onChange={handleOptionChange}
              placeholder="ttf,woff,svg,png,jpg,gif,jpeg,ico"
            />
          </label>
        </div>
        
        <div className="option-group">
          <label>
            <input
              type="checkbox"
              name="verbose"
              checked={options.verbose}
              onChange={handleOptionChange}
            />
            详细输出
          </label>
        </div>
      </div>
      
      <div className="alert alert-info mt-3">
        <strong>优化提示：</strong> 扫描过程中，结果会实时更新。您可以随时点击下方链接查看当前进度。
      </div>
      
      <button 
        onClick={startScan} 
        disabled={isScanning}
        className="scan-button btn btn-primary"
      >
        {isScanning ? '扫描中...' : '开始 Gau 扫描'}
      </button>
      
      <div className="scan-info mt-3">
        <a 
          href={`/result/${userId}/${targetId}?type=gau`} 
          target="_blank" 
          rel="noopener noreferrer"
          className="btn btn-outline-secondary"
        >
          查看扫描结果
        </a>
      </div>
    </div>
  );
};

export default GauScan; 