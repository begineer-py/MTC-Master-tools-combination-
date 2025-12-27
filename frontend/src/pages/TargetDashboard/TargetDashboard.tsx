import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

// 1. 從 api.ts 引入通用工具
import { gqlFetcher, GET_TARGET_DETAIL_QUERY } from "../../services/api";

// 2. 從 api_seed.ts 引入種子專用服務
import { SeedService } from "../../services/api_seed";

import type { Target, Seed } from "../../type";
import "./TargetDashboard.css";

function TargetDashboard() {
  const navigate = useNavigate();
  // 【修正】這裡必須跟 App.tsx 的 :targetId 對應
  const { targetId } = useParams<{ targetId: string }>();

  // 【修正】強制轉為數字，後續所有 API 調用都用這個 numericId
  const numericId = Number(targetId);

  // 狀態
  const [target, setTarget] = useState<Target | null>(null);
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 新增種子表單
  const [newSeedVal, setNewSeedVal] = useState("");
  const [newSeedType, setNewSeedType] = useState("DOMAIN");
  const [isAdding, setIsAdding] = useState(false);

  // === 讀取 (Fetch Data) ===
  const fetchDetails = async () => {
    // 檢查數字是否有效
    if (!numericId || isNaN(numericId)) return;

    setLoading(true);
    try {
      const data = await gqlFetcher<{ core_target_by_pk: Target }>(
        GET_TARGET_DETAIL_QUERY,
        { id: numericId } // 傳入數字
      );

      if (!data.core_target_by_pk) {
        setError("目標不存在或已被刪除");
        setLoading(false);
        return;
      }

      setTarget(data.core_target_by_pk);
      setSeeds(data.core_target_by_pk.core_seeds || []);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "無法獲取情報");
    } finally {
      setLoading(false);
    }
  };

  // === 寫入 (Add Seed) ===
  const handleAddSeed = async () => {
    if (!newSeedVal.trim()) return;
    if (!numericId) return;

    setIsAdding(true);
    try {
      // 這裡傳入 numericId
      await SeedService.add(numericId, {
        value: newSeedVal.trim(),
        type: newSeedType,
      });
      setNewSeedVal("");
      // 成功後重新拉取列表
      fetchDetails();
    } catch (err: any) {
      alert(`添加失敗: ${err.message}`); // 修正錯誤訊息獲取方式
    } finally {
      setIsAdding(false);
    }
  };

  // === 刪除 (Delete Seed) ===
  const handleDeleteSeed = async (seedId: number) => {
    if (!window.confirm("確認移除此種子？")) return;
    try {
      await SeedService.delete(seedId);
      setSeeds((prev) => prev.filter((s) => s.id !== seedId));
    } catch (err) {
      alert("刪除失敗");
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [numericId]);

  if (isNaN(numericId))
    return (
      <div style={{ padding: 20, color: "#d32f2f" }}>INVALID TARGET ID</div>
    );
  if (loading && !target)
    return (
      <div style={{ padding: 20, color: "#888" }}>
        INITIALIZING DASHBOARD...
      </div>
    );
  if (error)
    return <div style={{ padding: 20, color: "#d32f2f" }}>ERROR: {error}</div>;
  if (!target) return null;

  return (
    <div className="td-container">
      {/* 標頭 */}
      <header className="td-header">
        <div style={{ display: "flex", alignItems: "center" }}>
          <button onClick={() => navigate("/")} className="td-back-btn">
            ← BACK
          </button>
          <div>
            <h1 style={{ margin: 0, fontSize: "1.5rem" }}>
              {target.name}{" "}
              <span style={{ fontSize: "0.6em", color: "#666" }}>
                // OPERATION DASHBOARD
              </span>
            </h1>
            <div style={{ color: "#888", fontSize: "0.9rem", marginTop: 5 }}>
              {target.description || "No description"}
            </div>
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "0.8rem", color: "#666" }}>TARGET ID</div>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: "1.2rem",
              color: "var(--primary)",
            }}
          >
            {target.id}
          </div>
        </div>
      </header>

      <div className="td-layout">
        {/* 左側：種子清單 */}
        <div className="td-main">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 10,
            }}
          >
            <h3 style={{ margin: 0 }}>SEEDS ({seeds.length})</h3>
            <button
              onClick={fetchDetails}
              style={{
                background: "none",
                border: "none",
                color: "#2196f3",
                cursor: "pointer",
              }}
            >
              REFRESH
            </button>
          </div>

          {seeds.length === 0 ? (
            <div
              style={{
                padding: 40,
                border: "2px dashed #333",
                textAlign: "center",
                color: "#666",
              }}
            >
              NO SEEDS CONFIGURED.
              <br />
              Add a Root Domain or IP on the right to start reconnaissance.
            </div>
          ) : (
            <table className="seed-table">
              <thead>
                <tr>
                  {/* [修改 1] 新增 ID 表頭 */}
                  <th style={{ width: "60px", color: "#666" }}>ID</th>

                  <th>TYPE</th>
                  <th>VALUE</th>
                  <th>ADDED</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {seeds.map((seed) => (
                  <tr key={seed.id}>
                    {/* ID 欄位 */}
                    <td
                      style={{
                        fontFamily: "monospace",
                        color: "#666",
                        fontSize: "0.9em",
                      }}
                    >
                      #{seed.id}
                    </td>

                    {/* 類型欄位 */}
                    <td style={{ width: "80px" }}>
                      <span
                        className={`seed-type-badge ${
                          seed.type === "DOMAIN" ? "type-domain" : "type-ip"
                        }`}
                      >
                        {seed.type}
                      </span>
                    </td>

                    {/* 值欄位 */}
                    <td>
                      <span className="seed-value">{seed.value}</span>
                    </td>

                    {/* 時間欄位 */}
                    <td style={{ color: "#666", fontSize: "0.85rem" }}>
                      {new Date(seed.created_at).toLocaleString()}
                    </td>

                    {/* --- [修正重點] 動作欄位 --- */}
                    <td style={{ width: "140px", textAlign: "center" }}>
                      {/* 1. Recon 按鈕 (只有 DOMAIN 顯示) */}
                      {seed.type === "DOMAIN" && (
                        <button
                          onClick={() =>
                            navigate(
                              `/target/${target.id}/seed/${seed.id}/subdomain`
                            )
                          }
                          style={{
                            marginRight: "10px",
                            background: "none",
                            border: "1px solid #2196f3",
                            color: "#2196f3",
                            cursor: "pointer",
                            padding: "4px 8px", // 稍微調大一點好點擊
                            fontSize: "0.8rem",
                            borderRadius: "3px",
                          }}
                          title="Open Recon Dashboard"
                        >
                          RECON 🎯
                        </button>
                      )}

                      {/* 2. 刪除按鈕 */}
                      <button
                        className="btn-icon-del"
                        onClick={() => handleDeleteSeed(seed.id)}
                        title="Remove Seed"
                      >
                        ×
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* 右側：添加面板 */}
        <div className="td-sidebar">
          <h3
            style={{
              marginTop: 0,
              borderBottom: "1px solid #444",
              paddingBottom: 10,
            }}
          >
            ADD SEED
          </h3>

          <label
            style={{
              display: "block",
              color: "#888",
              marginBottom: 5,
              fontSize: "0.85rem",
            }}
          >
            Seed Value
          </label>
          <input
            type="text"
            className="input-dark"
            placeholder="e.g. example.com"
            value={newSeedVal}
            onChange={(e) => setNewSeedVal(e.target.value)}
          />

          <label
            style={{
              display: "block",
              color: "#888",
              marginBottom: 5,
              fontSize: "0.85rem",
            }}
          >
            Type
          </label>
          <select
            className="select-dark"
            value={newSeedType}
            onChange={(e) => setNewSeedType(e.target.value)}
          >
            <option value="DOMAIN">DOMAIN</option>
            <option value="IP">IP ADDRESS</option>
            <option value="URL">URL</option>
          </select>

          <button
            className="btn-add"
            onClick={handleAddSeed}
            disabled={isAdding}
          >
            {isAdding ? "ADDING..." : "ADD SEED +"}
          </button>

          <div style={{ marginTop: 20, fontSize: "0.8rem", color: "#666" }}>
            <p>
              <strong>NOTE:</strong>
            </p>
            Adding a seed will automatically trigger:
            <ul style={{ paddingLeft: 20, marginTop: 5 }}>
              <li>Subdomain Enumeration</li>
              <li>Port Scanning</li>
              <li>Tech Stack Analysis</li>
            </ul>
            (Feature pending...)
          </div>
        </div>
      </div>
    </div>
  );
}

export default TargetDashboard;
