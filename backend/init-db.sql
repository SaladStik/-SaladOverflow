-- Initialize SaladOverflow Database
-- This script runs when the MariaDB container starts for the first time
-- Create the test database
CREATE DATABASE IF NOT EXISTS saladoverflow_test;

-- Grant permissions to salad_user on both databases
GRANT ALL PRIVILEGES ON saladoverflow.* TO 'salad_user'@'%';

GRANT ALL PRIVILEGES ON saladoverflow_test.* TO 'salad_user'@'%';

-- Flush privileges to ensure they take effect
FLUSH PRIVILEGES;

-- Create a simple test table to verify connection
USE saladoverflow;

CREATE TABLE
    IF NOT EXISTS connection_test (
        id INT AUTO_INCREMENT PRIMARY KEY,
        message VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

INSERT INTO
    connection_test (message)
VALUES
    ('Database initialized successfully!');

-- Display initialization message
SELECT
    'SaladOverflow database initialized successfully!' AS status;