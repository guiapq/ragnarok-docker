CREATE DATABASE IF NOT EXISTS ragnarok;
USE ragnarok;

-- Tabela de Speedrun para Torneios e Eventos
CREATE TABLE IF NOT EXISTS event_speedruns (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    char_id INT UNSIGNED NOT NULL UNIQUE,
    name VARCHAR(30) NOT NULL,
    class SMALLINT UNSIGNED NOT NULL,
    base_level INT UNSIGNED NOT NULL DEFAULT 99,
    job_level INT UNSIGNED NOT NULL DEFAULT 50,
    total_seconds INT UNSIGNED NOT NULL,
    achieved_at DATETIME NOT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabela de Abates de MVP para Torneios e Bounty Hunting
CREATE TABLE IF NOT EXISTS event_mvp_kills (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    char_id INT UNSIGNED NOT NULL,
    char_name VARCHAR(30) NOT NULL,
    mob_id INT UNSIGNED NOT NULL,
    mob_name VARCHAR(50) NOT NULL,
    killed_at DATETIME NOT NULL,
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL,
    INDEX idx_char_id (char_id),
    INDEX idx_mob_id (mob_id),
    INDEX idx_killed_at (killed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Conta de Administrador GM Fixa (roadmin, roadmin)
INSERT INTO `login` (`account_id`, `userid`, `user_pass`, `sex`, `email`, `group_id`, `state`, `unban_time`, `expiration_time`, `logincount`, `lastlogin`, `last_ip`, `birthdate`, `character_slots`, `pincode`, `pincode_change`, `vip_time`, `old_group`)
VALUES (2000001, 'roadmin', 'roadmin', 'M', 'admin@ragnarogue.local', 99, 0, 0, 0, 0, NULL, '', '2000-01-01', 9, '', 0, 0, 0)
ON DUPLICATE KEY UPDATE `user_pass` = 'roadmin', `group_id` = 99;