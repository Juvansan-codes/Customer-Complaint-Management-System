CREATE DATABASE IF NOT EXISTS complaint_db;
USE complaint_db;

DROP TABLE IF EXISTS remarks;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role ENUM('Admin', 'Agent', 'Customer') NOT NULL,
    avatar VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT NOW()
) ENGINE=InnoDB;

CREATE TABLE tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    category VARCHAR(50),
    complaint TEXT NOT NULL,
    screenshot VARCHAR(255) DEFAULT NULL,
    priority ENUM('High', 'Medium', 'Low') DEFAULT 'Low',
    status ENUM('Open', 'In Progress', 'Closed') DEFAULT 'Open',
    assigned_to INT DEFAULT NULL,
    created_at DATETIME DEFAULT NOW(),
    resolved_at DATETIME DEFAULT NULL,
    FOREIGN KEY (customer_id) REFERENCES users(user_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    customer_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    given_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
    FOREIGN KEY (customer_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE remarks (
    remark_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    agent_id INT NOT NULL,
    note TEXT NOT NULL,
    added_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id),
    FOREIGN KEY (agent_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

INSERT INTO users (username, password, email, role)
VALUES (
    'admin',
    '$2b$12$FWiwiKFxtTkK4cZ6DXHHbuuAtZ89evg2ayDQZ7rMvA5U1Uu8dRE1K',
    'admin@complaint.local',
    'Admin'
)
ON DUPLICATE KEY UPDATE username = VALUES(username);
