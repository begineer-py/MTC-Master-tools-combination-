

export const GLOBAL_CONFIG = {
    // Django 後端地址 (寫入操作)
    DJANGO_API_BASE: 'http://127.0.0.1:8000/api',
  
    // Hasura GraphQL 地址 (讀取操作)
    HASURA_GRAPHQL_URL: 'http://127.0.0.1:8085/v1/graphql',
  
    // Hasura Admin Secret
    // 注意：這必須與你 docker-compose.yml 中 HASURA_GRAPHQL_ADMIN_SECRET 的值完全一致
    // 為了方便開發者直接啟動，我們預設使用這個簡單的密鑰
    HASURA_ADMIN_SECRET: 'YourSuperStrongAdminSecretHere',
  };