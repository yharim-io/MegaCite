-- 初始化数据库脚本: 可直接粘贴到 mysql 客户端执行
-- 本脚本会创建数据库 `megacite`（若不存在），并建立所需表及约束。
CREATE DATABASE IF NOT EXISTS `megacite` DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
USE `megacite`;

-- 为避免重复执行报错，先删除可能已存在的表（按外键依赖顺序）
DROP TABLE IF EXISTS url_mappings;
DROP TABLE IF EXISTS post_references;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS auth_platforms;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    token VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE auth_platforms (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    -- [修复] Cookie 数据极大，VARCHAR(255) 必定报错，改为 LONGTEXT
    credential LONGTEXT DEFAULT NULL,
    UNIQUE KEY ux_user_platform (user_id, platform),
    CONSTRAINT fk_auth_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cid VARCHAR(32) UNIQUE NOT NULL,
    owner_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    `context` LONGTEXT,
    description TEXT,
    category VARCHAR(255) NOT NULL DEFAULT 'default',
    date DATE NOT NULL,
    -- 确保同一个用户在同一个 category 下的 title 不重复
    -- 现在的 URL 结构是 username/category/title，因此需要这个联合唯一约束
    UNIQUE KEY ux_owner_category_title (owner_id, category, title),
    CONSTRAINT fk_post_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE post_references (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_cid VARCHAR(32) NOT NULL,
    ref_cid VARCHAR(32) NOT NULL,
    INDEX idx_post_cid (post_cid),
    INDEX idx_ref_cid (ref_cid),
    CONSTRAINT fk_ref_post FOREIGN KEY (post_cid) REFERENCES posts(cid) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE url_mappings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cid VARCHAR(32) NOT NULL,
    url_path VARCHAR(255) NOT NULL,
    UNIQUE KEY ux_cid (cid),
    UNIQUE KEY ux_url_path (url_path),
    CONSTRAINT fk_map_cid FOREIGN KEY (cid) REFERENCES posts(cid) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER USER 'root'@'localhost' IDENTIFIED BY '114514';
FLUSH PRIVILEGES;