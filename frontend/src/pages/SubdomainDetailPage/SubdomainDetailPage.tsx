import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { gqlFetcher } from "../../services/api";
import { GET_SUBDOMAIN_DETAIL_QUERY } from "../../services/subdomains_detail";
import { AiAnalysisService } from "../../services/api_ai";
import type { SubdomainIntelResponse } from "../../type";
import "./SubdomainDetailPage.css";

// 布爾值顯示組件
const BooleanDisplay: React.FC<{ value: boolean }> = ({ value }) => (
  <span
    className={value ? "info-value boolean-true" : "info-value boolean-false"}
  >
    {value ? "TRUE" : "FALSE"}
  </span>
);
// [新增] 可复制命令行的组件
const CommandAction: React.FC<{ command: string }> = ({ command }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000); // 2秒后恢复状态
  };
  return (
    <div className="command-action-item">
      <pre className="command-text">{command}</pre>
      <button onClick={handleCopy} className="btn-copy">
        {copied ? "COPIED!" : "COPY"}
      </button>
    </div>
  );
};
function SubdomainDetailPage() {
  const { targetId, subdomainId } = useParams();
  const navigate = useNavigate();
  const nSubdomainId = Number(subdomainId);

  // === 狀態聲明 (只聲明一次) ===
  const [intel, setIntel] = useState<SubdomainIntelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // === 數據獲取函數 (只定義一次) ===
  const fetchData = () => {
    if (!nSubdomainId) return;
    setLoading(true);
    gqlFetcher<SubdomainIntelResponse>(GET_SUBDOMAIN_DETAIL_QUERY, {
      subdomain_id: nSubdomainId,
    })
      .then((data) => setIntel(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  // === 觸發 AI 分析函數 (只定義一次) ===
  const handleRequestAiAnalysis = async () => {
    if (!intel?.core_subdomain_by_pk) return;

    setIsAnalyzing(true);
    try {
      const response = await AiAnalysisService.analyzeSubdomains([
        intel.core_subdomain_by_pk.name,
      ]);
      alert(`AI 分析任務已提交: ${response.detail}`);
      setTimeout(fetchData, 5000); // 5秒後刷新數據
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // === Effect Hook (只用一個) ===
  // 這個 useEffect 負責在組件加載或 subdomainId 變化時獲取數據
  useEffect(() => {
    fetchData();
  }, [nSubdomainId]);

  // === 渲染前的守衛條件 (Guard Clauses) ===
  if (loading) return <div>Loading Subdomain Intel...</div>;
  if (!intel || !intel.core_subdomain_by_pk)
    return <div>Subdomain not found.</div>;

  // === 數據準備 (只準備一次) ===
  const subdomain = intel.core_subdomain_by_pk;
  const aiAnalysis = subdomain.core_subdomainaianalysis;
  const relatedUrls = intel.core_urlresult.filter((url) =>
    url.url.includes(subdomain.name)
  );
  return (
    <div className="sdd-container">
      {/* 標頭 */}
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>{subdomain.name}</h1>
        <div style={{ color: "#888" }}>Subdomain Deep-Dive Analysis</div>
      </div>

      <div className="sdd-layout">
        {/* 左側主情報區 */}
        <main className="sdd-main">
          {/* 基礎情報 */}
          <div className="info-card">
            <div className="info-card-header">Basic Information</div>
            <div className="info-card-body info-grid">
              <div className="info-item">
                <span className="info-label">ID</span>{" "}
                <span className="info-value">{subdomain.id}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Active</span>{" "}
                <BooleanDisplay value={subdomain.is_active} />
              </div>
              <div className="info-item">
                <span className="info-label">Resolvable</span>{" "}
                <BooleanDisplay value={subdomain.is_resolvable} />
              </div>
              <div className="info-item">
                <span className="info-label">CNAME</span>{" "}
                <span className="info-value">{subdomain.cname || "N/A"}</span>
              </div>
            </div>
          </div>

          {/* 安全情報 */}
          <div className="info-card">
            <div className="info-card-header">Security Posture</div>
            <div className="info-card-body info-grid">
              <div className="info-item">
                <span className="info-label">Behind CDN</span>{" "}
                <BooleanDisplay value={subdomain.is_cdn} />
              </div>
              <div className="info-item">
                <span className="info-label">CDN Name</span>{" "}
                <span className="info-value">
                  {subdomain.cdn_name || "N/A"}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Behind WAF</span>{" "}
                <BooleanDisplay value={subdomain.is_waf} />
              </div>
              <div className="info-item">
                <span className="info-label">WAF Name</span>{" "}
                <span className="info-value">
                  {subdomain.waf_name || "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* 關聯資產 */}
          <div className="info-card">
            <div className="info-card-header">Associated Assets</div>
            <div className="info-card-body">
              <div className="info-item" style={{ marginBottom: 15 }}>
                <span className="info-label">Resolved IPs</span>
                <div className="asset-list">
                  {" "}
                  {/* 使用 asset-list 容器 */}
                  {subdomain.core_subdomain_ips.length > 0 ? (
                    subdomain.core_subdomain_ips.map(({ core_ip }) => (
                      <div key={core_ip.id} className="asset-item">
                        <span className="asset-icon">🌐</span>
                        <a
                          href={`/target/${targetId}/ip/${core_ip.id}`}
                          className="asset-link ip-link"
                        >
                          {core_ip.ipv4 || core_ip.ipv6}
                        </a>
                      </div>
                    ))
                  ) : (
                    <span className="text-muted">None</span>
                  )}
                </div>
              </div>
              <div className="info-item">
                <span className="info-label">Related URLs</span>
                <div className="asset-list">
                  {relatedUrls.length > 0 ? (
                    relatedUrls.map((u) => (
                      <div key={u.id} className="asset-item">
                        <span className="asset-icon">🔗</span>
                        <a
                          href={`/target/${targetId}/url/${u.id}`}
                          className="asset-link url-link"
                        >
                          {u.url}
                        </a>
                      </div>
                    ))
                  ) : (
                    <span className="text-muted">None</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
        {/* 右側 AI 分析 */}
        <aside className="sdd-sidebar">
          <div className="info-card ai-card">
            <div className="info-card-header">AI-Powered Tactical Briefing</div>

            {aiAnalysis ? (
              // === 渲染完整的分析结果 ===
              <div className="info-card-body">
                <div className="risk-score-container">
                  <span className="info-label">Risk Score</span>
                  <div className="risk-score">{aiAnalysis.risk_score}</div>
                </div>

                <div className="info-item">
                  <span className="info-label">Executive Summary</span>
                  <p className="ai-summary">{aiAnalysis.summary}</p>
                </div>

                <div className="info-item">
                  <span className="info-label">Inferred Purpose</span>
                  <p className="ai-summary">{aiAnalysis.inferred_purpose}</p>
                </div>

                <div className="info-item">
                  <span className="info-label">Business Impact</span>
                  <p className="ai-summary">{aiAnalysis.business_impact}</p>
                </div>

                <div className="info-item">
                  <span className="info-label">Tech Stack Summary</span>
                  <p className="ai-summary">{aiAnalysis.tech_stack_summary}</p>
                </div>

                <div className="info-item">
                  <span className="info-label">Potential Vulnerabilities</span>
                  <div className="pre-box">
                    {/* 将数组转换成带项目符号的列表字符串 */}
                    {aiAnalysis.potential_vulnerabilities
                      .map((vuln) => `- ${vuln}`)
                      .join("\n")}
                  </div>
                </div>

                <div className="info-item">
                  <span className="info-label">Recommended Actions</span>
                  <div className="pre-box">
                    {aiAnalysis.recommended_actions
                      .map((action) => `• ${action}`)
                      .join("\n")}
                  </div>
                </div>

                <div className="info-item">
                  <span className="info-label">Immediate Command Actions</span>
                  {aiAnalysis.command_actions.map((cmd, index) => (
                    <CommandAction key={index} command={cmd} />
                  ))}
                </div>
              </div>
            ) : (
              // === 渲染请求按钮 ===
              <div className="info-card-body ai-placeholder">
                <p>No analysis data available for this subdomain.</p>
                <button
                  className="btn-ai-trigger"
                  onClick={handleRequestAiAnalysis}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? "SUBMITTING..." : "REQUEST AI ANALYSIS"}
                </button>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default SubdomainDetailPage;
