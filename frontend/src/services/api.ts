import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';
import type { Target, CreateTargetPayload, UpdateTargetPayload } from '../type';

// ==========================================
// 1. Django API (Axios) - 負責 Target 寫入 (CUD)
// ==========================================

const djangoApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/targets`, 
  headers: {
    'Content-Type': 'application/json',
  },
});

export const TargetService = {
  create: async (payload: CreateTargetPayload) => {
    return await djangoApi.post<Target>('/', payload);
  },
  update: async (id: number, payload: UpdateTargetPayload) => {
    return await djangoApi.put<Target>(`/${id}`, payload);
  },
  delete: async (id: number) => {
    return await djangoApi.delete(`/${id}`);
  },
};

// ==========================================
// 2. Hasura GraphQL (Fetch) - 負責讀取 (Read)
// ==========================================

export const gqlFetcher = async <T>(query: string, variables: any = {}): Promise<T> => {
  try {
    const response = await fetch(GLOBAL_CONFIG.HASURA_GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
      },
      body: JSON.stringify({ query, variables }),
    });

    const result = await response.json();

    if (result.errors) {
      const msg = result.errors[0]?.message || 'GraphQL Error';
      throw new Error(msg);
    }

    return result.data;
  } catch (error) {
    console.error("GraphQL Request Failed:", error);
    throw error;
  }
};

// === Query Definitions ===

// 用於首頁列表
export const GET_TARGETS_QUERY = `
  query GetTargets {
    core_target(order_by: {created_at: desc}) {
      id
      name
      description
      created_at
    }
  }
`;

// [關鍵修正] 用於詳情頁，包含 seeds 關聯
export const GET_TARGET_DETAIL_QUERY = `
  query GetTargetDetail($id: bigint!) {
    core_target_by_pk(id: $id) {
      id
      name
      description
      created_at
      core_seeds(order_by: {created_at: desc}) {
        id
        value
        type
        is_active
        created_at
      }
    }
  }
`;