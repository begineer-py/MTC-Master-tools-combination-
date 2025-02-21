export const formatNmapResults = (data) => {
  if (!data) return null;

  const portStats = {
    open: 0,
    filtered: 0,
    closed: 0
  };

  if (data.ports) {
    Object.values(data.ports).forEach(port => {
      portStats[port.state]++;
    });
  }

  return {
    host: data.host || '未知',
    hostname: data.hostname || '未知',
    state: data.state || '未知',
    scan_time: data.scan_time || '未知',
    portStats,
    ports: data.ports || {}
  };
};

export const formatCrtshResults = (data) => {
  if (!data) return null;

  return {
    scan_time: data.scan_time ? new Date(data.scan_time * 1000).toLocaleString() : '未知',
    domains: data.domains || [],
    total: data.domains?.length || 0
  };
};

export const formatWebtechResults = (data) => {
  if (!data || !data.technologies) return null;

  const techByCategory = {};
  data.technologies.forEach(tech => {
    tech.categories.forEach(category => {
      if (!techByCategory[category]) {
        techByCategory[category] = [];
      }
      techByCategory[category].push({
        name: tech.name,
        version: tech.version || '未知',
        confidence: tech.confidence
      });
    });
  });

  return {
    target_url: data.target_url,
    scan_time: data.scan_time,
    technologies: techByCategory
  };
};

export const formatParamSpiderResults = (data) => {
  if (!data) return null;

  return {
    total_urls: data.total_urls || 0,
    unique_parameters: data.unique_parameters || 0,
    result_text: data.result_text || '',
    id: data.id
  };
};

export const formatFlareSolverrResults = (data) => {
  if (!data) return null;

  return {
    version: data.version || 'N/A',
    uptime: data.uptime || 'N/A',
    is_cloudflare: data.is_cloudflare || false,
    message: data.message || ''
  };
};

// ... 其他格式化函數 ... 