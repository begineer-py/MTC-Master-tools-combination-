-- 先禁用外鍵約束檢查，否則有依賴的表無法刪除
-- SET session_replication_role = 'replica'; 

-- 動態生成 DROP TABLE 語句，並執行
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tableowner = 'myuser') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE;';
    END LOOP;
END $$;

-- 重新啟用外鍵約束檢查
-- SET session_replication_role = 'origin';