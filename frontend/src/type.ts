// src/type.ts

// === 基础枚举和 Payload ===
export type ScanStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
export type ScanMode = 'DOMAIN' | 'IP' | 'URL';

export interface CreateTargetPayload {
  name: string;
  description?: string;
}

export interface UpdateTargetPayload {
  name?: string;
  description?: string;
}

export interface AddSeedPayload {
  value: string;
  type?: string;
}

export interface DomainReconTriggerPayload {
  seed_id: number;
}


// === 核心数据模型 ===
export interface Target {
  id: number;
  name: string;
  description?: string | null;
  created_at: string;
  core_seeds?: Seed[];
}

export interface Seed {
  id: number;
  target_id: number;
  value: string;
  type: string;
  is_active: boolean;
  created_at: string;
}

export interface IP {
  id: number;
  ipv4?: string | null;
  ipv6?: string | null;
}

export interface Subdomain {
  id: number;
  name: string;
  created_at: string;
}

export interface UrlResult {
  id: number;
  url: string;
  content_length?: number;
  content_fetch_status?: string;
}

// === 扫描记录模型 ===
export interface SubfinderScan {
  id: number;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  added_count?: number;
}

export interface NmapScan {
  id: number;
  status: ScanStatus;
  completed_at?: string | null;
  target_ip_id: number;
}

export interface UrlScan {
  id: number;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
}

// === AI 分析结果模型 ===
export interface SubdomainAIAnalysis {
  risk_score: number;
  summary: string;
  business_impact: string;
  inferred_purpose: string;
  tech_stack_summary: string;
  potential_vulnerabilities: string[];
  recommended_actions: string[];
  command_actions: string[];
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  raw_response?: any;
}

// === GraphQL 聚合响应模型 ===

// -- 用於 SeedReconPage --
export interface SeedIntelligenceData extends Seed {
  core_nmapscans: NmapScan[];
  core_subfinderscans: SubfinderScan[];
  core_subdomains: Subdomain[];
}
export interface SeedIntelligenceResponse {
  core_seed: SeedIntelligenceData[];
  core_ip: IP[];
  core_urlscan: UrlScan[];
  core_urlresult: UrlResult[];
}

// -- 用於 SubdomainDetailPage --
export interface SubdomainDetail extends Subdomain {
  is_active: boolean;
  is_resolvable: boolean;
  is_cdn: boolean;
  is_waf: boolean;
  cname?: string | null;
  cdn_name?: string | null;
  waf_name?: string | null;
  core_subdomain_ips: {
    ip_id: number;
    core_ip: IP;
  }[];
  // 修正：根据上个 issue，这里应该是对象而不是数组
  core_subdomainaianalysis: SubdomainAIAnalysis | null; 
}
export interface SubdomainIntelResponse {
  core_subdomain_by_pk: SubdomainDetail;
  core_urlresult: UrlResult[];
}