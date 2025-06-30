-- 確保表哥和你小子已經存在，如果不存在，需要先插入或根據需要調整
-- 為了完整演示，我們假設表現在是空的，先插入這些數據
INSERT INTO users (username, email, password_hash, is_admin) 
VALUES 
    ('小美', 'xiaomei@example.com', 'password456', FALSE),
    ('管理員', 'admin@example.com', 'admin_password', TRUE),
    ('小華', 'xiaohua@example.com', 'password789', FALSE);

-- R: Read (讀取)
SELECT * FROM users; -- 查詢所有數據

SELECT username, email FROM users WHERE is_admin = TRUE; -- 查詢管理員信息

-- U: Update (更新)
UPDATE users SET email = 'new_email@example.com' WHERE username = '小美';

-- 確認更新結果
SELECT * FROM users WHERE username = '小美';

-- D: Delete (刪除)
DELETE FROM users WHERE username = '小美';

-- 確認刪除結果，小美應該沒了
SELECT * FROM users;

-- 再刪除一個
DELETE FROM users WHERE username = '小華';

-- 最後再查詢一次，只剩管理員
SELECT * FROM users;