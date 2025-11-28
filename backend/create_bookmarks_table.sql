CREATE TABLE
    IF NOT EXISTS bookmarks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        post_id INT NOT NULL,
        user_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_post (user_id, post_id),
        INDEX idx_post_id (post_id),
        INDEX idx_user_id (user_id)
    ) ENGINE = InnoDB;