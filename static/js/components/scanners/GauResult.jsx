import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../common/LoadingSpinner';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const GauResult = ({ userId, targetId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [downloadingFile, setDownloadingFile] = useState(false);
  const [scanStatus, setScanStatus] = useState('未知');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [urlCategories, setUrlCategories] = useState({});
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [pageLoading, setPageLoading] = useState(false);

  // 获取扫描结果
  const fetchResults = async () => {
    try {
      setError(null);
      
      // 首先只获取元数据
      const metadataResponse = await fetch(`/api/gau/result/${userId}/${targetId}?metadata=only`);
      const metadataData = await metadataResponse.json();
      
      if (!metadataResponse.ok) {
        throw new Error(metadataData.message || '获取结果失败');
      }
      
      if (metadataData.success && metadataData.result) {
        // 更新状态和元数据
        const resultData = metadataData.result;
        setScanStatus(resultData.status);
        setLastUpdated(new Date().toLocaleTimeString());
        
        // 如果扫描完成或失败，获取完整结果（包括分类统计）
        if (resultData.status === 'completed' || resultData.status === 'failed') {
          // 构建查询参数
          const queryParams = new URLSearchParams({
            page: currentPage,
            per_page: itemsPerPage,
            category: activeCategory,
            ...(searchTerm && { search: searchTerm })
          }).toString();
          
          const fullResponse = await fetch(`/api/gau/result/${userId}/${targetId}?${queryParams}`);
          const fullData = await fullResponse.json();
          
          if (fullData.success && fullData.result) {
            setResult(fullData.result);
            
            // 如果有分类数据，更新分类
            if (fullData.result.categories) {
              setUrlCategories(fullData.result.categories);
            }
          }
        } else {
          // 如果扫描仍在进行中，只更新基本信息
          setResult(prevResult => ({
            ...prevResult,
            ...resultData,
            urls: prevResult?.urls || []
          }));
        }
      } else {
        setResult(null);
        setScanStatus('未知');
      }
    } catch (err) {
      setError(err.message);
      toast.error(`获取结果失败: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 加载特定页面的数据
  const loadPage = async (page) => {
    if (!result) return;
    
    try {
      setPageLoading(true);
      
      // 构建查询参数
      const queryParams = new URLSearchParams({
        page: page,
        per_page: itemsPerPage,
        category: activeCategory,
        ...(searchTerm && { search: searchTerm })
      }).toString();
      
      const response = await fetch(`/api/gau/result/${userId}/${targetId}?${queryParams}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || '获取页面数据失败');
      }
      
      if (data.success && data.result) {
        // 更新当前页面的URL
        setResult(prevResult => ({
          ...prevResult,
          urls: data.result.urls,
          pagination: data.result.pagination
        }));
        
        setCurrentPage(page);
      }
    } catch (err) {
      toast.error(`加载页面失败: ${err.message}`);
    } finally {
      setPageLoading(false);
    }
  };

  // 切换分类
  const changeCategory = async (category) => {
    setActiveCategory(category);
    setCurrentPage(1);
    
    try {
      setPageLoading(true);
      
      // 构建查询参数
      const queryParams = new URLSearchParams({
        page: 1,
        per_page: itemsPerPage,
        category: category,
        ...(searchTerm && { search: searchTerm })
      }).toString();
      
      const response = await fetch(`/api/gau/result/${userId}/${targetId}?${queryParams}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || '获取分类数据失败');
      }
      
      if (data.success && data.result) {
        // 更新URL和分页信息
        setResult(prevResult => ({
          ...prevResult,
          urls: data.result.urls,
          pagination: data.result.pagination
        }));
      }
    } catch (err) {
      toast.error(`切换分类失败: ${err.message}`);
    } finally {
      setPageLoading(false);
    }
  };

  // 搜索URL
  const handleSearch = async () => {
    try {
      setPageLoading(true);
      
      // 构建查询参数
      const queryParams = new URLSearchParams({
        page: 1,
        per_page: itemsPerPage,
        category: activeCategory,
        ...(searchTerm && { search: searchTerm })
      }).toString();
      
      const response = await fetch(`/api/gau/result/${userId}/${targetId}?${queryParams}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || '搜索失败');
      }
      
      if (data.success && data.result) {
        // 更新URL和分页信息
        setResult(prevResult => ({
          ...prevResult,
          urls: data.result.urls,
          pagination: data.result.pagination
        }));
        
        setCurrentPage(1);
      }
    } catch (err) {
      toast.error(`搜索失败: ${err.message}`);
    } finally {
      setPageLoading(false);
    }
  };

  // 分页
  const paginate = (pageNumber) => {
    loadPage(pageNumber);
  };

  // 自动刷新
  useEffect(() => {
    fetchResults();
    
    // 如果扫描正在进行中，设置自动刷新
    let intervalId;
    if (autoRefresh && (scanStatus === 'scanning' || scanStatus === 'pending')) {
      intervalId = setInterval(() => {
        fetchResults();
      }, 10000); // 增加刷新间隔到10秒
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [userId, targetId, scanStatus, autoRefresh]);

  // 监听搜索词变化
  useEffect(() => {
    const delaySearch = setTimeout(() => {
      if (searchTerm !== '') {
        handleSearch();
      }
    }, 800); // 增加延迟到800毫秒
    
    return () => clearTimeout(delaySearch);
  }, [searchTerm]);

  // 获取当前页的URL
  const getCurrentUrls = () => {
    if (!result || !result.urls) {
      return [];
    }
    
    return result.urls;
  };

  // 渲染分页
  const renderPagination = () => {
    if (!result || !result.pagination) {
      return null;
    }
    
    const { page, total_pages } = result.pagination;
    
    if (total_pages <= 1) {
      return null;
    }
    
    const pageNumbers = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, page - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(total_pages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }
    
    return (
      <nav aria-label="分页导航">
        <ul className="pagination justify-content-center">
          <li className={`page-item ${page === 1 ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => paginate(1)}
              disabled={page === 1 || pageLoading}
            >
              首页
            </button>
          </li>
          <li className={`page-item ${page === 1 ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => paginate(page - 1)}
              disabled={page === 1 || pageLoading}
            >
              上一页
            </button>
          </li>
          
          {pageNumbers.map(number => (
            <li key={number} className={`page-item ${page === number ? 'active' : ''}`}>
              <button 
                className="page-link" 
                onClick={() => paginate(number)}
                disabled={pageLoading}
              >
                {number}
              </button>
            </li>
          ))}
          
          <li className={`page-item ${page === total_pages ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => paginate(page + 1)}
              disabled={page === total_pages || pageLoading}
            >
              下一页
            </button>
          </li>
          <li className={`page-item ${page === total_pages ? 'disabled' : ''}`}>
            <button 
              className="page-link" 
              onClick={() => paginate(total_pages)}
              disabled={page === total_pages || pageLoading}
            >
              末页
            </button>
          </li>
        </ul>
      </nav>
    );
  };

  // 渲染分类标签
  const renderCategories = () => {
    if (!result || !result.categories) {
      return null;
    }
    
    const categories = result.categories;
    
    return (
      <div className="url-categories mb-3">
        <div className="d-flex flex-wrap">
          {Object.keys(categories).map(category => (
            <button
              key={category}
              className={`btn btn-sm me-2 mb-2 ${activeCategory === category ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => changeCategory(category)}
              disabled={pageLoading}
            >
              {category === 'all' ? '全部' : category}
              <span className="badge bg-light text-dark ms-1">
                {categories[category] || 0}
              </span>
            </button>
          ))}
        </div>
      </div>
    );
  };

  // 下载结果
  const downloadResults = async () => {
    try {
      setDownloadingFile(true);
      
      const response = await fetch(`/api/gau/file/${userId}/${targetId}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || '下载文件失败');
      }
      
      // 获取文件内容
      const blob = await response.blob();
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      
      // 设置文件名
      const domain = result?.domain || 'domain';
      a.download = `gau_results_${domain}.txt`;
      
      // 添加到文档并触发点击
      document.body.appendChild(a);
      a.click();
      
      // 清理
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('文件下载成功');
    } catch (err) {
      toast.error(`下载文件失败: ${err.message}`);
      setError(err.message);
    } finally {
      setDownloadingFile(false);
    }
  };

  // 获取状态文本
  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return '等待中';
      case 'scanning':
        return '扫描中';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      default:
        return '未知';
    }
  };

  // 获取状态类
  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'scanning':
      case 'pending':
        return 'pending';
      case 'failed':
        return 'error';
      default:
        return '';
    }
  };

  // 刷新结果
  const refreshResults = () => {
    setLoading(true);
    fetchResults();
  };

  return (
    <div className="container mt-4">
      <ToastContainer position="top-right" autoClose={3000} />
      
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3>Gau扫描结果</h3>
          <div>
            <button 
              className="btn btn-sm btn-outline-primary me-2" 
              onClick={refreshResults}
              disabled={loading}
            >
              <i className="fas fa-sync-alt me-1"></i> 刷新
            </button>
            <div className="form-check form-switch d-inline-block ms-2">
              <input
                className="form-check-input"
                type="checkbox"
                id="autoRefreshSwitch"
                checked={autoRefresh}
                onChange={() => setAutoRefresh(!autoRefresh)}
              />
              <label className="form-check-label" htmlFor="autoRefreshSwitch">
                自动刷新
              </label>
            </div>
          </div>
        </div>
        
        <div className="card-body">
          {loading ? (
            <LoadingSpinner message="正在加载扫描结果..." />
          ) : error ? (
            <div className="alert alert-danger">{error}</div>
          ) : !result ? (
            <div className="alert alert-info">没有找到扫描结果</div>
          ) : (
            <div>
              <div className="row mb-4">
                <div className="col-md-6">
                  <div className="card">
                    <div className="card-body">
                      <h5 className="card-title">扫描信息</h5>
                      <p className="mb-1"><strong>目标域名:</strong> {result.domain}</p>
                      <p className="mb-1">
                        <strong>状态:</strong> 
                        <span className={`status-indicator ${getStatusClass(result.status)} ms-2`}>
                          {getStatusText(result.status)}
                        </span>
                      </p>
                      <p className="mb-1"><strong>URL总数:</strong> {result.total_urls}</p>
                      <p className="mb-1"><strong>扫描时间:</strong> {result.scan_time}</p>
                      {lastUpdated && (
                        <p className="mb-1"><strong>最后更新:</strong> {lastUpdated}</p>
                      )}
                      {result.error_message && (
                        <div className="alert alert-danger mt-2">
                          <strong>错误:</strong> {result.error_message}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="col-md-6">
                  <div className="card">
                    <div className="card-body">
                      <h5 className="card-title">操作</h5>
                      <button 
                        className="btn btn-primary me-2" 
                        onClick={downloadResults}
                        disabled={downloadingFile || !result.urls || result.urls.length === 0}
                      >
                        {downloadingFile ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                            下载中...
                          </>
                        ) : (
                          <>
                            <i className="fas fa-download me-1"></i> 下载结果
                          </>
                        )}
                      </button>
                      
                      <a 
                        href={`/user/${userId}/attack/${targetId}`} 
                        className="btn btn-outline-secondary"
                      >
                        <i className="fas fa-arrow-left me-1"></i> 返回扫描页面
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              
              {result.urls && result.urls.length > 0 ? (
                <div>
                  <div className="mb-3">
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control"
                        placeholder="搜索URL..."
                        value={searchTerm}
                        onChange={(e) => {
                          setSearchTerm(e.target.value);
                          setCurrentPage(1);
                        }}
                      />
                      {searchTerm && (
                        <button
                          className="btn btn-outline-secondary"
                          type="button"
                          onClick={() => {
                            setSearchTerm('');
                            setCurrentPage(1);
                          }}
                        >
                          <i className="fas fa-times"></i>
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {renderCategories()}
                  
                  <div className="url-list">
                    {getCurrentUrls().length > 0 ? (
                      <div className="list-group">
                        {getCurrentUrls().map((url, index) => (
                          <div key={index} className="list-group-item url-item">
                            <a href={url} target="_blank" rel="noopener noreferrer">
                              {url}
                            </a>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="alert alert-info">
                        {searchTerm ? '没有匹配的URL' : '该分类下没有URL'}
                      </div>
                    )}
                  </div>
                  
                  {renderPagination()}
                  
                  <div className="mt-3 text-muted text-center">
                    显示 {urlCategories[activeCategory]?.length || 0} 个URL中的 
                    {getCurrentUrls().length} 个
                    {searchTerm && ` (搜索: "${searchTerm}")`}
                  </div>
                </div>
              ) : (
                <div className="alert alert-info">
                  {result.status === 'scanning' || result.status === 'pending' ? (
                    <>
                      <LoadingSpinner size="small" />
                      <span>扫描正在进行中，请稍候...</span>
                    </>
                  ) : (
                    '没有找到URL'
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GauResult; 