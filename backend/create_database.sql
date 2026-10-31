-- Initial local database setup. Run in MySQL Workbench as an administrator.
-- Replace the password placeholder with a new long alphanumeric password before running.
CREATE DATABASE IF NOT EXISTS careerlens CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'careerlens_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_NEW_LONG_RANDOM_PASSWORD';
ALTER USER 'careerlens_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_NEW_LONG_RANDOM_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
ON careerlens.* TO 'careerlens_app'@'localhost';
DROP USER IF EXISTS 'careerlens_app'@'127.0.0.1';
FLUSH PRIVILEGES;
