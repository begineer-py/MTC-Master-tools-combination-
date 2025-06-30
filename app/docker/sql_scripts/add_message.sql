INSERT INTO users (username, email, password_hash, is_admin) 
VALUES ('表哥', 'biaoge@example.com', 'hashed_password_for_biaoge', TRUE); -- 第一個用戶

INSERT INTO users (username, email, password_hash) 
VALUES ('你小子', 'nixiaozi@example.com', 'hashed_password_for_nixiaozi'); -- 第二個用戶
SELECT * FROM users;