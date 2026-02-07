USE studenthub_db;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS conversations (
  id INT NOT NULL AUTO_INCREMENT,
  type ENUM('direct','group') NOT NULL DEFAULT 'direct',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS conversation_participants (
  id INT NOT NULL AUTO_INCREMENT,
  conversation_id INT NOT NULL,
  user_id INT NOT NULL,
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_cp_conversation
    FOREIGN KEY (conversation_id)
    REFERENCES conversations(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_cp_user
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,
  UNIQUE KEY uq_conversation_user (conversation_id, user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS messages (
  id INT NOT NULL AUTO_INCREMENT,
  conversation_id INT NOT NULL,
  sender_id INT NOT NULL,
  content TEXT NOT NULL,
  message_type ENUM('text') DEFAULT 'text',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_deleted TINYINT(1) DEFAULT 0,
  PRIMARY KEY (id),
  CONSTRAINT fk_msg_conversation
    FOREIGN KEY (conversation_id)
    REFERENCES conversations(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_msg_sender
    FOREIGN KEY (sender_id)
    REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
