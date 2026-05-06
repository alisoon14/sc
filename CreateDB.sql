-- --------------------------------------------------------
-- Хост:                         10.77.129.34
-- Версия сервера:               10.11.14-MariaDB-0+deb12u2-log - Debian 12
-- Операционная система:         debian-linux-gnu
-- HeidiSQL Версия:              12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Дамп структуры базы данных work_schedule_db
CREATE DATABASE IF NOT EXISTS `work_schedule_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `work_schedule_db`;

-- Дамп структуры для таблица work_schedule_db.ActualShiftTimes
CREATE TABLE IF NOT EXISTS `ActualShiftTimes` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Уникальный идентификатор записи',
  `user_name` varchar(255) NOT NULL COMMENT 'Имя пользователя',
  `tguser` varchar(255) DEFAULT NULL COMMENT 'Telegram username пользователя',
  `actual_start_time` datetime NOT NULL COMMENT 'Фактическое время заступления на смену',
  `shift_date` date NOT NULL COMMENT 'Дата смены',
  `created_at` timestamp NULL DEFAULT current_timestamp() COMMENT 'Время создания записи',
  PRIMARY KEY (`id`),
  KEY `idx_tguser` (`tguser`),
  KEY `idx_shift_date` (`shift_date`),
  KEY `idx_user_name` (`user_name`),
  KEY `idx_actual_start_time` (`actual_start_time`)
) ENGINE=InnoDB AUTO_INCREMENT=418 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Хранит фактическое время заступления сотрудников на смену для дальнейшего анализа и отчетности';

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.Employees
CREATE TABLE IF NOT EXISTS `Employees` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT 'ФИО',
  `active` tinyint(1) DEFAULT 1 COMMENT 'Отображение в графике',
  `phone` text DEFAULT NULL COMMENT 'Телефон',
  `username` text DEFAULT NULL COMMENT 'Юзернейм ПК',
  `LastLoginTime` datetime DEFAULT NULL COMMENT 'Последний раз брал смену по боту',
  `tguser` text DEFAULT NULL COMMENT 'ТГ юзер',
  `mail` text DEFAULT NULL COMMENT 'Рабочая почта',
  `position` text DEFAULT NULL COMMENT 'Должность',
  `TechnitianIdSd` int(10) DEFAULT NULL COMMENT 'ID техникаSD',
  `onshift` int(11) DEFAULT 0 COMMENT 'Статус на смене',
  `telegram_id` bigint(20) DEFAULT NULL COMMENT 'ТГ айди',
  `grade` enum('Джуниор (Jun)','Специалист (Mid)','Продвинутый (Adv)') DEFAULT NULL COMMENT 'Грейд сотрудника ДС',
  `employment_date` date DEFAULT NULL COMMENT 'дата приёма на работу',
  `password_hash` varchar(255) DEFAULT NULL,
  `web_role` enum('user','admin') NOT NULL DEFAULT 'user',
  `web_last_login` timestamp NULL DEFAULT NULL,
  `web_created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=100007 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.Reminders
CREATE TABLE IF NOT EXISTS `Reminders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(255) DEFAULT NULL,
  `reminder_text` text DEFAULT NULL,
  `reminder_time` datetime DEFAULT NULL,
  `created_time` datetime DEFAULT current_timestamp(),
  `is_sent` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.RemoteLimitExtensions
CREATE TABLE IF NOT EXISTS `RemoteLimitExtensions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(50) NOT NULL,
  `month` int(11) NOT NULL,
  `year` int(11) NOT NULL,
  `added_by` varchar(50) NOT NULL,
  `reason` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_user_month` (`tguser`,`year`,`month`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.RemoteWorkRequests
CREATE TABLE IF NOT EXISTS `RemoteWorkRequests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(100) NOT NULL COMMENT 'Telegram username сотрудника',
  `shift_date` date NOT NULL COMMENT 'Дата смены для удаленной работы',
  `reason` text NOT NULL COMMENT 'Причина запроса удаленной работы',
  `status` enum('pending','approved','rejected') DEFAULT 'pending' COMMENT 'Статус запроса',
  `approved_by_lead` tinyint(1) DEFAULT 0 COMMENT 'Одобрено старшим инженером',
  `approved_by_manager` tinyint(1) DEFAULT 0 COMMENT 'Одобрено руководителем',
  `created_at` timestamp NULL DEFAULT current_timestamp() COMMENT 'Время создания запроса',
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'Время последнего обновления',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_date_active` (`tguser`,`shift_date`,`status`) COMMENT 'Один активный запрос на дату',
  KEY `idx_tguser` (`tguser`),
  KEY `idx_shift_date` (`shift_date`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=59 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Система запросов на удаленную работу с лимитом 1 раз в месяц и согласованием руководства';

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.Schedule
CREATE TABLE IF NOT EXISTS `Schedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `employee_id` int(11) DEFAULT NULL,
  `shift_type_id` int(11) DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  KEY `shift_type_id` (`shift_type_id`),
  CONSTRAINT `Schedule_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `Employees` (`id`),
  CONSTRAINT `Schedule_ibfk_2` FOREIGN KEY (`shift_type_id`) REFERENCES `ShiftTypes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2344 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.sent_notifications
CREATE TABLE IF NOT EXISTS `sent_notifications` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `request_id` varchar(50) NOT NULL,
  `notification_type` varchar(50) NOT NULL DEFAULT 'telegram',
  `sent_time` datetime NOT NULL DEFAULT current_timestamp(),
  `request_status` varchar(100) NOT NULL,
  `created_time` datetime NOT NULL,
  `last_updated_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_notification` (`request_id`,`notification_type`),
  KEY `idx_sent_time` (`sent_time`),
  KEY `idx_request_id` (`request_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1040 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Таблица для отслеживания отправленных уведомлений о заявках в Telegram';

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.ShiftExchange
CREATE TABLE IF NOT EXISTS `ShiftExchange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `schedule_id` int(11) NOT NULL,
  `initiator_tguser` varchar(50) NOT NULL,
  `recipient_tguser` varchar(50) NOT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `approved_by_recipient` tinyint(1) DEFAULT 0,
  `approved_by_lead` tinyint(1) DEFAULT 0,
  `approved_by_manager` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.ShiftNotes
CREATE TABLE IF NOT EXISTS `ShiftNotes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(255) DEFAULT NULL,
  `note_text` text DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.ShiftTypes
CREATE TABLE IF NOT EXISTS `ShiftTypes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `day_hours` int(11) NOT NULL,
  `night_hours` int(11) NOT NULL,
  `comment` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.shift_device_logs
CREATE TABLE IF NOT EXISTS `shift_device_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `web_user_id` int(11) DEFAULT NULL,
  `tguser` varchar(50) DEFAULT NULL,
  `shift_type` enum('office','remote') NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `ip_org` varchar(255) DEFAULT NULL COMMENT 'ISP / организация',
  `ip_country` varchar(100) DEFAULT NULL,
  `ip_city` varchar(100) DEFAULT NULL,
  `ip_is_vpn` tinyint(1) DEFAULT 0,
  `webrtc_local_ips` text DEFAULT NULL COMMENT 'JSON массив',
  `webrtc_public_ip` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `browser_name` varchar(100) DEFAULT NULL,
  `browser_version` varchar(50) DEFAULT NULL,
  `os_name` varchar(100) DEFAULT NULL,
  `os_version` varchar(50) DEFAULT NULL,
  `device_type` varchar(50) DEFAULT NULL COMMENT 'desktop/mobile/tablet',
  `screen_width` int(11) DEFAULT NULL,
  `screen_height` int(11) DEFAULT NULL,
  `screen_color_depth` int(11) DEFAULT NULL,
  `window_width` int(11) DEFAULT NULL,
  `window_height` int(11) DEFAULT NULL,
  `device_pixel_ratio` float DEFAULT NULL,
  `platform` varchar(100) DEFAULT NULL,
  `hardware_concurrency` int(11) DEFAULT NULL COMMENT 'кол-во CPU логических ядер',
  `device_memory` float DEFAULT NULL COMMENT 'RAM в GB',
  `timezone_name` varchar(100) DEFAULT NULL,
  `timezone_offset` int(11) DEFAULT NULL COMMENT 'минуты от UTC',
  `language_primary` varchar(20) DEFAULT NULL,
  `languages` text DEFAULT NULL COMMENT 'JSON массив',
  `cookie_enabled` tinyint(1) DEFAULT NULL,
  `do_not_track` varchar(10) DEFAULT NULL,
  `touch_support` tinyint(1) DEFAULT NULL,
  `max_touch_points` int(11) DEFAULT NULL,
  `pdf_viewer_enabled` tinyint(1) DEFAULT NULL,
  `canvas_fingerprint` varchar(64) DEFAULT NULL,
  `webgl_vendor` varchar(255) DEFAULT NULL,
  `webgl_renderer` varchar(255) DEFAULT NULL,
  `webgl_fingerprint` varchar(64) DEFAULT NULL,
  `audio_fingerprint` varchar(64) DEFAULT NULL,
  `fonts_hash` varchar(64) DEFAULT NULL,
  `battery_charging` tinyint(1) DEFAULT NULL,
  `battery_level` float DEFAULT NULL COMMENT '0.0 - 1.0',
  `connection_type` varchar(50) DEFAULT NULL,
  `connection_effective_type` varchar(20) DEFAULT NULL COMMENT '4g/3g/2g/slow-2g',
  `connection_downlink` float DEFAULT NULL COMMENT 'Мбит/с',
  `connection_rtt` int(11) DEFAULT NULL COMMENT 'мс',
  `geo_lat` decimal(10,8) DEFAULT NULL,
  `geo_lon` decimal(11,8) DEFAULT NULL,
  `geo_accuracy` float DEFAULT NULL COMMENT 'метры',
  `geo_altitude` float DEFAULT NULL,
  `geo_altitude_accuracy` float DEFAULT NULL,
  `geo_heading` float DEFAULT NULL,
  `geo_speed` float DEFAULT NULL,
  `geo_denied` tinyint(1) DEFAULT NULL,
  `is_office_ip` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'IP из офисного диапазона',
  `is_office_network` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'WebRTC показывает офисную сеть',
  `suspicion_flags` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'список подозрительных признаков' CHECK (json_valid(`suspicion_flags`)),
  `trust_score` int(11) NOT NULL DEFAULT 50 COMMENT '0-100: 100 = точно офис',
  `raw_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`raw_data`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_tguser` (`tguser`),
  KEY `idx_created` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.TimeToCompReq
CREATE TABLE IF NOT EXISTS `TimeToCompReq` (
  `created_time` datetime DEFAULT NULL,
  `last_updated_time` datetime DEFAULT NULL,
  `request_id` int(11) DEFAULT NULL,
  `employee_on_shift` varchar(255) DEFAULT NULL COMMENT 'Сотрудник, который был на смене во время обработки заявки',
  `time_to_assignment` int(11) DEFAULT NULL COMMENT 'Время от создания до назначения заявки в секундах'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.web_audit_logs
CREATE TABLE IF NOT EXISTS `web_audit_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `actor_user_id` int(11) DEFAULT NULL,
  `actor_username` varchar(100) DEFAULT NULL,
  `actor_name` varchar(255) DEFAULT NULL,
  `actor_tguser` varchar(100) DEFAULT NULL,
  `actor_role` varchar(20) DEFAULT NULL,
  `method` varchar(10) NOT NULL,
  `path` varchar(500) NOT NULL,
  `endpoint` varchar(150) DEFAULT NULL,
  `full_url` text DEFAULT NULL,
  `query_params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`query_params`)),
  `form_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`form_data`)),
  `json_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`json_data`)),
  `route_params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`route_params`)),
  `uploaded_files` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`uploaded_files`)),
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `referer` text DEFAULT NULL,
  `status_code` smallint(6) NOT NULL,
  `duration_ms` int(11) DEFAULT NULL,
  `is_admin_area` tinyint(1) NOT NULL DEFAULT 0,
  `summary` varchar(255) DEFAULT NULL,
  `extra` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`extra`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_actor_user` (`actor_user_id`),
  KEY `idx_actor_username` (`actor_username`),
  KEY `idx_method` (`method`),
  KEY `idx_status` (`status_code`),
  KEY `idx_is_admin_area` (`is_admin_area`)
) ENGINE=InnoDB AUTO_INCREMENT=4696 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.web_notifications
CREATE TABLE IF NOT EXISTS `web_notifications` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(100) NOT NULL,
  `category` varchar(30) NOT NULL DEFAULT 'system',
  `event_type` varchar(80) NOT NULL,
  `title` varchar(255) NOT NULL,
  `body` text DEFAULT NULL,
  `link_url` varchar(255) DEFAULT NULL,
  `payload_json` mediumtext DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `read_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_notifications_user_created` (`tguser`,`created_at`),
  KEY `idx_notifications_user_read` (`tguser`,`is_read`),
  KEY `idx_notifications_type` (`event_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.web_push_subscriptions
CREATE TABLE IF NOT EXISTS `web_push_subscriptions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(100) NOT NULL,
  `endpoint` mediumtext NOT NULL,
  `endpoint_hash` char(64) NOT NULL,
  `p256dh` varchar(255) NOT NULL,
  `auth` varchar(255) NOT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `last_used_at` timestamp NULL DEFAULT NULL,
  `device_name` varchar(120) DEFAULT NULL,
  `device_platform` varchar(80) DEFAULT NULL,
  `device_lang` varchar(20) DEFAULT NULL,
  `device_tz` varchar(64) DEFAULT NULL,
  `device_fingerprint` char(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_tguser_endpoint` (`tguser`,`endpoint_hash`),
  KEY `idx_tguser_active` (`tguser`,`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=296 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.web_settings
CREATE TABLE IF NOT EXISTS `web_settings` (
  `key` varchar(100) NOT NULL,
  `value` text DEFAULT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

-- Дамп структуры для таблица work_schedule_db.web_shift_assignment_history
CREATE TABLE IF NOT EXISTS `web_shift_assignment_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tguser` varchar(100) NOT NULL,
  `shift_started_at` timestamp NOT NULL,
  `item_type` enum('request','task') NOT NULL,
  `external_id` varchar(100) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `link_url` varchar(255) DEFAULT NULL,
  `payload_json` mediumtext DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_assign_history_user_created` (`tguser`,`created_at`),
  KEY `idx_assign_history_shift_started` (`tguser`,`shift_started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Экспортируемые данные не выделены.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
