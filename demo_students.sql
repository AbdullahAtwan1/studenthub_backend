-- ==========================================================
--  DEMO STUDENTS DATA FOR STUDENTHUB
--  Database: studenthub_db
--  Table: demo_students
--  Prepared for Birzeit University Project
-- ==========================================================

CREATE DATABASE IF NOT EXISTS studenthub_db;
USE studenthub_db;

-- Drop table if exists
DROP TABLE IF EXISTS demo_students;

-- Create demo_students table
CREATE TABLE demo_students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    college VARCHAR(150),
    major VARCHAR(150),
    minor VARCHAR(150)
);

-- ==========================================================
--  FACULTY OF ENGINEERING & TECHNOLOGY
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1201001', 'Ahmad Nasser', 'Faculty of Engineering and Technology', 'Civil Engineering', NULL),
('1201002', 'Leen Barghouthi', 'Faculty of Engineering and Technology', 'Electrical Engineering', 'Physics'),
('1201003', 'Mohammad Odeh', 'Faculty of Engineering and Technology', 'Computer Systems Engineering', NULL),
('1201004', 'Aya Musleh', 'Faculty of Engineering and Technology', 'Mechanical Engineering', NULL),
('1201005', 'Tareq Zaid', 'Faculty of Engineering and Technology', 'Architectural Engineering', NULL);

-- ==========================================================
--  FACULTY OF SCIENCE
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1202001', 'Razan Qawasmeh', 'Faculty of Science', 'Biology', NULL),
('1202002', 'Omar Abu Saleh', 'Faculty of Science', 'Chemistry', 'Environmental Science'),
('1202003', 'Rama Shaheen', 'Faculty of Science', 'Mathematics', NULL),
('1202004', 'Mazen Atwan', 'Faculty of Science', 'Physics', NULL),
('1202005', 'Hala Abed', 'Faculty of Science', 'Biochemistry', NULL);

-- ==========================================================
--  FACULTY OF BUSINESS & ECONOMICS
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1203001', 'Yousef Daraghmeh', 'Faculty of Business and Economics', 'Accounting', NULL),
('1203002', 'Sara Khalil', 'Faculty of Business and Economics', 'Finance and Banking', NULL),
('1200449', 'Ali Saleh', 'Faculty of Business and Economics', 'Marketing', 'E-Commerce'),
('1203004', 'Mariam Hamdan', 'Faculty of Business and Economics', 'Economics', NULL),
('1203005', 'Khaled Abu Rmeileh', 'Faculty of Business and Economics', 'Business Administration', NULL);

-- ==========================================================
--  FACULTY OF INFORMATION TECHNOLOGY
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1201997', 'Abdullah Atwan', 'Faculty of Information Technology', 'Computer Science', 'Artificial Intelligence'),
('1204002', 'Sama Kurdi', 'Faculty of Information Technology', 'Computer Information Systems', NULL),
('1200449', 'Salah Awwad', 'Faculty of Information Technology', 'Data Science', NULL),
('1204004', 'Lina Abu Awad', 'Faculty of Information Technology', 'Software Engineering', NULL),
('1204005', 'Ola Zboun', 'Faculty of Information Technology', 'Network Engineering', NULL);

-- ==========================================================
--  FACULTY OF LAW & PUBLIC ADMINISTRATION
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1205001', 'Hassan Sarsour', 'Faculty of Law and Public Administration', 'Public Administration', NULL),
('1205002', 'Reem Taha', 'Faculty of Law and Public Administration', 'Political Science', 'Sociology'),
('1205003', 'Mahmoud Younis', 'Faculty of Law and Public Administration', 'Law', NULL),
('1205004', 'Lama Salman', 'Faculty of Law and Public Administration', 'Public Policy', NULL),
('1205005', 'Hadeel Hijazi', 'Faculty of Law and Public Administration', 'International Relations', NULL);

-- ==========================================================
--  FACULTY OF ARTS
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1206001', 'Noor Jaber', 'Faculty of Arts', 'English Language and Literature', NULL),
('1206002', 'Yazan Suleiman', 'Faculty of Arts', 'Arabic Language and Literature', NULL),
('1206003', 'Rola Saadeh', 'Faculty of Arts', 'History', NULL),
('1206004', 'Amjad Abu Hamed', 'Faculty of Arts', 'Geography', NULL),
('1206005', 'Dana Khaled', 'Faculty of Arts', 'Translation', NULL);

-- ==========================================================
--  FACULTY OF PHARMACY, NURSING & HEALTH PROFESSIONS
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1207001', 'Aya Khatib', 'Faculty of Pharmacy, Nursing and Health Professions', 'Pharmacy', NULL),
('1207002', 'Abed Alrahman Ali', 'Faculty of Pharmacy, Nursing and Health Professions', 'Nursing', NULL),
('1207003', 'Leila Shalabi', 'Faculty of Pharmacy, Nursing and Health Professions', 'Physiotherapy', NULL),
('1207004', 'Ahmad Rashed', 'Faculty of Pharmacy, Nursing and Health Professions', 'Medical Laboratory Sciences', NULL),
('1207005', 'Rama Abdeen', 'Faculty of Pharmacy, Nursing and Health Professions', 'Nutrition and Dietetics', NULL);

-- ==========================================================
--  FACULTY OF EDUCATION
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1208001', 'Abeer Qadomi', 'Faculty of Education', 'Primary Education', NULL),
('1208002', 'Razan Sbeihat', 'Faculty of Education', 'Kindergarten Education', NULL),
('1208003', 'Mohammad Barakat', 'Faculty of Education', 'Educational Psychology', NULL),
('1208004', 'Hadeel Anabtawi', 'Faculty of Education', 'Special Education', NULL),
('1208005', 'Omar Mansour', 'Faculty of Education', 'Teaching English as a Foreign Language', NULL);

-- ==========================================================
--  ADDITIONAL RANDOM STUDENTS FOR TESTING
-- ==========================================================
INSERT INTO demo_students (student_id, full_name, college, major, minor) VALUES
('1209001', 'Fatima Al Masri', 'Faculty of Science', 'Physics', NULL),
('1209002', 'Yara Fakhouri', 'Faculty of Information Technology', 'Computer Science', 'Cybersecurity'),
('1209003', 'Anas Jarrar', 'Faculty of Business and Economics', 'Finance and Banking', NULL),
('1209004', 'Hind Shaheen', 'Faculty of Law and Public Administration', 'Law', NULL),
('1209005', 'Ola Jaber', 'Faculty of Arts', 'Translation', NULL);


