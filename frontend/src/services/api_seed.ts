// src/services/api_seed.ts

import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';
import type { Seed, AddSeedPayload } from '../type';

/**
 * 創建一個專門用於 Seed 操作的 Axios 實例
 * 雖然 baseURL 可以直接用 /api/targets，但為了清晰，我們在具體方法裡拼接路徑。
 */
const djangoApi = axios.create({
  baseURL: GLOBAL_CONFIG.DJANGO_API_BASE, // 例如: http://127.0.0.1:8000/api
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000, // 設置 5 秒超時，避免請求卡死
});

export const SeedService = {
  /**
   * 為指定目標新增種子
   * @param targetId 目標 ID
   * @param payload 種子數據 (value, type)
   * 
   * 對應後端: POST /api/targets/{target_id}/seeds
   */
  add: async (targetId: number, payload: AddSeedPayload): Promise<Seed> => {
    try {
      // 這裡路徑要小心，後端 router 是掛在 /targets 下
      // 所以完整路徑是 /targets/{id}/seeds
      const response = await djangoApi.post<Seed>(`/targets/${targetId}/seeds`, payload);
      return response.data;
    } catch (error: any) {
      console.error('API Error: Failed to add seed', error.response?.data || error.message);
      // 將後端錯誤訊息拋出，讓前端 UI 可以顯示具體原因 (如: 種子已存在)
      throw new Error(error.response?.data?.message || '添加種子失敗');
    }
  },

  /**
   * 刪除指定種子
   * @param seedId 種子 ID
   * 
   * 對應後端: DELETE /api/targets/seeds/{seed_id}
   */
  delete: async (seedId: number): Promise<void> => {
    try {
      // 根據 api.py: @router.delete("/seeds/{seed_id}")
      // 完整路徑是 /targets/seeds/{seed_id}
      await djangoApi.delete(`/targets/seeds/${seedId}`);
    } catch (error: any) {
      console.error('API Error: Failed to delete seed', error);
      throw new Error('刪除種子失敗');
    }
  },

  /**
   * (可選) 獲取指定目標的所有種子
   * 雖然我們通常用 GraphQL 獲取，但有時候單獨拉取列表也很方便
   * 
   * 對應後端: GET /api/targets/{target_id}/seeds
   */
  listByTarget: async (targetId: number): Promise<Seed[]> => {
    try {
      const response = await djangoApi.get<Seed[]>(`/targets/${targetId}/seeds`);
      return response.data;
    } catch (error) {
      console.error('API Error: Failed to list seeds', error);
      return [];
    }
  }
};