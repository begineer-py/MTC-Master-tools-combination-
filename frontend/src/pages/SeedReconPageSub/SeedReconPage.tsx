import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom"; // 雖然 navigate 少用了，但 hook 仍可能需要保留以防擴展
import { gqlFetcher } from "../../services/api";
import {
  ReconService,
  GET_SEED_ULTIMATE_INTEL_QUERY,
} from "../../services/api_recon";
import type {
  SeedIntelligenceResponse,
  SeedIntelligenceData,
  Subdomain,
  IP,
  UrlResult,
} from "../../type";
import "./SeedReconPage.css";

// 可折疊卡片組件 (保持不變)
const AssetCard: React.FC<{
  title: string;
  count: number;
  children: React.ReactNode;
}> = ({ title, count, children }) => {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className="assets-card">
      <div className="assets-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="assets-title">{title}</div>
        <div>
          <span className="assets-count">{count}</span>
          <span className={`assets-toggle ${isOpen ? "expanded" : ""}`}>▼</span>
        </div>
      </div>
      {isOpen && <div className="assets-content">{children}</div>}
    </div>
  );
};

function SeedReconPage() {
  const { targetId, seedId } = useParams();
  const navigate = useNavigate();
  const nSeedId = Number(seedId);

  const [intel, setIntel] = useState<SeedIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const fetchIntel = async () => {
    if (!nSeedId) return;
    try {
      const data = await gqlFetcher<SeedIntelligenceResponse>(
        GET_SEED_ULTIMATE_INTEL_QUERY,
        { seed_id: nSeedId }
      );
      setIntel(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartScan = async () => {
    if (!nSeedId) return;
    setTriggering(true);
    try {
      // 呼叫後端 API 觸發掃描
      await ReconService.startDomainRecon(nSeedId);
      // 延遲一秒後刷新，給後端時間創建 PENDING 記錄
      setTimeout(fetchIntel, 1000);
    } catch (err: any) {
      alert(`指令被拒絕: ${err.message}`);
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchIntel();
    const interval = setInterval(fetchIntel, 10000);
    return () => clearInterval(interval);
  }, [nSeedId]);

  if (loading) return <div>LOADING INTEL...</div>;
  if (!intel || intel.core_seed.length === 0) return <div>SEED NOT FOUND</div>;

  const seedData: SeedIntelligenceData = intel.core_seed[0];
  const isRunning = seedData.core_subfinderscans.some(
    (s) => s.status === "PENDING" || s.status === "RUNNING"
  );

  return (
    <div className="recon-container">
      {/* Header */}
      <div className="recon-header-card">
        <div>
          <div className="seed-info-large">{seedData.value}</div>
          <div style={{ color: "#666" }}>ID: {seedData.id}</div>
        </div>
        <button
          className="btn-fire"
          onClick={handleStartScan}
          disabled={triggering || isRunning}
        >
          {triggering
            ? "INITIATING..."
            : isRunning
            ? "SCAN RUNNING"
            : "START RECON"}
        </button>
      </div>

      {/* 掃描記錄 */}
      <AssetCard
        title="Subdomain Scans"
        count={seedData.core_subfinderscans.length}
      >
        {seedData.core_subfinderscans.length > 0 ? (
          <div className="scan-history-list">
            {seedData.core_subfinderscans.map((scan) => (
              <div key={scan.id} className="scan-item">
                <span style={{ fontFamily: "monospace", color: "#666" }}>
                  #{scan.id}
                </span>
                <span className={`status-badge status-${scan.status}`}>
                  {scan.status}
                </span>
                <span>New Found: {scan.added_count}</span>
                <span style={{ color: "#888", fontSize: "0.9em" }}>
                  {new Date(scan.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state-message">No scan records.</div>
        )}
      </AssetCard>

      {/* === 渲染所有資產 === */}
      <h3 style={{ marginTop: 30 }}>DISCOVERED ASSETS</h3>

      {/* 子域名資產 */}
      <AssetCard title="Subdomains" count={seedData.core_subdomains.length}>
        {seedData.core_subdomains.length > 0 ? (
          <table className="assets-table">
            <thead>
              <tr>
                <th>NAME</th>
                <th>DISCOVERED AT</th>
                <th>TO DETAIL</th>
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {seedData.core_subdomains.map((sub: Subdomain) => (
                <tr key={sub.id}>
                  <td>{sub.name}</td>
                  <td>{new Date(sub.created_at).toLocaleString()}</td>
                  <td>
                    {/* [修正] 使用標準 <a> 標籤，保留按鈕樣式 */}
                    <a
                      href={`/target/${targetId}/subdomain/${sub.id}`}
                      className="btn btn-ghost btn-sm"
                      style={{ textDecoration: "none" }} // 確保按鈕樣式不被下劃線破壞
                    >
                      Detail
                    </a>
                  </td>
                  <td>{sub.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state-message">No subdomains found.</div>
        )}
      </AssetCard>

      <AssetCard title="IP Addresses" count={intel.core_ip.length}>
        {intel.core_ip.length > 0 ? (
          <table className="assets-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>IP ADDRESS</th>
              </tr>
            </thead>
            <tbody>
              {intel.core_ip.map((ip: IP) => (
                <tr key={ip.id}>
                  <td>{ip.id}</td>
                  <td>
                    {/* [修正] 使用標準 <a> 標籤，移除 onClick 攔截，與 SubdomainDetail 保持一致 */}
                    <a
                      href={`/target/${targetId}/ip/${ip.id}`}
                      className="asset-link ip-link"
                    >
                      {ip.ipv4 || ip.ipv6}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state-message">No IP addresses found.</div>
        )}
      </AssetCard>

      {/* URL 資產 */}
      <AssetCard title="URLs Found" count={intel.core_urlresult.length}>
        {intel.core_urlresult.length > 0 ? (
          <table className="assets-table">
            <thead>
              <tr>
                <th>URL</th>
                <th>DETAILS</th>
              </tr>
            </thead>
            <tbody>
              {intel.core_urlresult.map((url: UrlResult) => (
                <tr key={url.id}>
                  <td>
                    {/* 外部鏈接保持不變 */}
                    <a
                      href={url.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="asset-link url-link"
                    >
                      {url.url}
                    </a>
                  </td>
                  <td>
                    {/* [修正] 使用標準 <a> 標籤，指向內部詳情頁 */}
                    <a
                      href={`/target/${targetId}/url/${url.id}`}
                      className="btn btn-ghost btn-sm"
                      style={{ textDecoration: "none" }}
                    >
                      Detail
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state-message">No URLs found.</div>
        )}
      </AssetCard>
    </div>
  );
}

export default SeedReconPage;
