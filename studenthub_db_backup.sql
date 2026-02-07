-- MySQL dump 10.13  Distrib 9.4.0, for macos14.7 (x86_64)
--
-- Host: localhost    Database: studenthub_db
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- ------------------------------------------------------
-- Table structure for table `demo_students`
-- ------------------------------------------------------

DROP TABLE IF EXISTS `demo_students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;

CREATE TABLE `demo_students` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` varchar(20) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `college` varchar(150) DEFAULT NULL,
  `major` varchar(150) DEFAULT NULL,
  `minor` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;

-- ------------------------------------------------------
-- Dumping data for table `demo_students`
-- ------------------------------------------------------

LOCK TABLES `demo_students` WRITE;
/*!40000 ALTER TABLE `demo_students` DISABLE KEYS */;

INSERT INTO `demo_students` VALUES
(1,'1201001','Ahmad Nasser','Faculty of Engineering and Technology','Civil Engineering',NULL),
(2,'1201002','Leen Barghouthi','Faculty of Engineering and Technology','Electrical Engineering','Physics'),
(3,'1201003','Mohammad Odeh','Faculty of Engineering and Technology','Computer Systems Engineering',NULL),
(4,'1201004','Aya Musleh','Faculty of Engineering and Technology','Mechanical Engineering',NULL),
(5,'1201005','Tareq Zaid','Faculty of Engineering and Technology','Architectural Engineering',NULL),
(6,'1202001','Razan Qawasmeh','Faculty of Science','Biology',NULL),
(7,'1202002','Omar Abu Saleh','Faculty of Science','Chemistry','Environmental Science'),
(8,'1202003','Rama Shaheen','Faculty of Science','Mathematics',NULL),
(9,'1202004','Mazen Atwan','Faculty of Science','Physics',NULL),
(10,'1202005','Hala Abed','Faculty of Science','Biochemistry',NULL),
(11,'1203001','Yousef Daraghmeh','Faculty of Business and Economics','Accounting',NULL),
(12,'1203002','Sara Khalil','Faculty of Business and Economics','Finance and Banking',NULL),
(13,'1203003','Ali Saleh','Faculty of Business and Economics','Marketing','E-Commerce'),
(14,'1203004','Mariam Hamdan','Faculty of Business and Economics','Economics',NULL),
(15,'1203005','Khaled Abu Rmeileh','Faculty of Business and Economics','Business Administration',NULL),
(16,'1204001','Abdullah Atwan','Faculty of Information Technology','Computer Science','Artificial Intelligence'),
(17,'1204002','Sama Kurdi','Faculty of Information Technology','Computer Information Systems',NULL),
(18,'1204003','Salah Awwad','Faculty of Information Technology','Data Science',NULL),
(19,'1204004','Lina Abu Awad','Faculty of Information Technology','Software Engineering',NULL),
(20,'1204005','Ola Zboun','Faculty of Information Technology','Network Engineering',NULL);

 /*!40000 ALTER TABLE `demo_students` ENABLE KEYS */;
UNLOCK TABLES;

-- ------------------------------------------------------
-- Table structure for table `users`
-- ------------------------------------------------------

DROP TABLE IF EXISTS `users`;
/*!50503 SET character_set_client = utf8mb4 */;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` varchar(20) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `is_verified` tinyint(1) DEFAULT NULL,
  `student_card_url` varchar(255) DEFAULT NULL,
  `college` varchar(150) DEFAULT NULL,
  `major` varchar(150) DEFAULT NULL,
  `minor` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`),
  UNIQUE KEY `email` (`email`),
  KEY `ix_users_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ------------------------------------------------------
-- Table structure for table `otps`
-- ------------------------------------------------------

DROP TABLE IF EXISTS `otps`;

CREATE TABLE `otps` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `code` varchar(6) NOT NULL,
  `purpose` enum('signup','forgot_password') NOT NULL,
  `expires_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `otps_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ------------------------------------------------------
-- Chat System Tables
-- ------------------------------------------------------

CREATE TABLE IF NOT EXISTS `conversations` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `type` ENUM('direct','group') NOT NULL DEFAULT 'direct',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `conversation_participants` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `conversation_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `joined_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_conversation_user` (`conversation_id`, `user_id`),
  CONSTRAINT `fk_cp_conversation`
    FOREIGN KEY (`conversation_id`)
    REFERENCES `conversations` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_cp_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `messages` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `conversation_id` INT NOT NULL,
  `sender_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `message_type` ENUM('text') DEFAULT 'text',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `is_deleted` TINYINT(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_msg_conversation`
    FOREIGN KEY (`conversation_id`)
    REFERENCES `conversations` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_msg_sender`
    FOREIGN KEY (`sender_id`)
    REFERENCES `users` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------
-- Final cleanup
-- ------------------------------------------------------

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed successfully