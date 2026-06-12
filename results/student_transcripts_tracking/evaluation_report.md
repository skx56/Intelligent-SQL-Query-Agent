# 🤖 Multi-Agent RAG Text-to-SQL Evaluation

**Database:** student_transcripts_tracking  
**Total Questions:** 64  
**Date:** 2025-12-21 19:32

---

## 📊 Summary - 3 Pipeline Comparison

| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |
|----------|-------------------|-----------------|-----------------|----------|
| **Single Agent** | 48.4% | 48.4% | 75.0% | 4.2s |
| **Multi Agent** | 60.9% | 60.9% | 79.4% | 10.1s |
| **Multi Agent RAG** | 62.5% | 62.5% | 80.6% | 21.6s |

### 🏆 Best: Multi Agent RAG (62.5%)

---

## 📈 Component Matching

| Pipeline | SELECT | FROM | WHERE | GROUP BY | ORDER BY |
|----------|--------|------|-------|----------|----------|
| Single Agent | 97% | 48% | 81% | 86% | 62% |
| Multi Agent | 84% | 73% | 89% | 91% | 59% |
| Multi Agent RAG | 88% | 72% | 89% | 86% | 69% |

---

## 📝 Detailed Results

### Q1 🟢
**what are all the addresses including line 1 and line 2?**
```sql
-- Gold: SELECT line_1 ,  line_2 FROM addresses
```
- **Single_Agent** ❌: `SELECT 
    A.line_1,
    A.line_2
FROM 
    Addresses A
JOI...`
- **Multi_Agent** ❌: `SELECT * FROM Addresses;...`
- **Multi_Agent_RAG** ✅: `SELECT line_1, line_2 FROM Addresses;...`

### Q2 🟢
**What is the first and second line for all addresses?**
```sql
-- Gold: SELECT line_1 ,  line_2 FROM addresses
```
- **Single_Agent** ✅: `SELECT T1.line_1, T1.line_2 FROM Addresses AS T1...`
- **Multi_Agent** ✅: `SELECT line_1, line_2 FROM Addresses;...`
- **Multi_Agent_RAG** ❌: `SELECT line_1, line_2 FROM Addresses ORDER BY address_id LIM...`

### Q3 🟢
**How many courses in total are listed?**
```sql
-- Gold: SELECT count(*) FROM Courses
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.course_id) FROM Courses AS T1 INNER...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM Courses;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Courses;...`

### Q4 🟢
**How many courses are there?**
```sql
-- Gold: SELECT count(*) FROM Courses
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.course_id) FROM Courses AS T1 INNER...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM Courses;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Courses;...`

### Q5 🟢
**How is the math course described?**
```sql
-- Gold: SELECT course_description FROM Courses WHERE course_name  =  'math'
```
- **Single_Agent** ❌: `SELECT T1.course_description FROM Courses AS T1 INNER JOIN S...`
- **Multi_Agent** ✅: `SELECT c.course_description FROM Courses AS c WHERE c.course...`
- **Multi_Agent_RAG** ✅: `SELECT c.course_description FROM Courses AS c WHERE c.course...`

### Q6 🟢
**What are the descriptions for all the math courses?**
```sql
-- Gold: SELECT course_description FROM Courses WHERE course_name  =  'math'
```
- **Single_Agent** ✅: `SELECT T1.course_description FROM Courses AS T1 INNER JOIN S...`
- **Multi_Agent** ✅: `SELECT c.course_description FROM Courses AS c WHERE c.course...`
- **Multi_Agent_RAG** ❌: `SELECT course_description FROM Courses WHERE course_name = '...`

### Q7 🟢
**What is the zip code of the address in the city Port Chelsea?**
```sql
-- Gold: SELECT zip_postcode FROM Addresses WHERE city  =  'Port Chelsea'
```
- **Single_Agent** ❌: `SELECT T1.zip_postcode FROM Addresses AS T1 INNER JOIN Depar...`
- **Multi_Agent** ❌: `SELECT T1.zip_postcode FROM Addresses AS T1 JOIN Cities AS T...`
- **Multi_Agent_RAG** ❌: `SELECT T1.zip_postcode FROM Addresses AS T1 JOIN Cities AS T...`

### Q8 🟢
**What is the zip code for Port Chelsea?**
```sql
-- Gold: SELECT zip_postcode FROM Addresses WHERE city  =  'Port Chelsea'
```
- **Single_Agent** ❌: `SELECT T1.zip_postcode FROM Addresses AS T1 INNER JOIN Cours...`
- **Multi_Agent** ❌: `SELECT T1.zip_postcode FROM Addresses AS T1 WHERE T1.line_1 ...`
- **Multi_Agent_RAG** ❌: `SELECT zip_postcode FROM Addresses WHERE line_1 = 'Port Chel...`

### Q9 🟡
**Which department offers the most number of degrees? List department name and id.**
```sql
-- Gold: SELECT T2.department_name ,  T1.department_id FROM Degree_Programs AS T1 JOIN Departments AS T2 ON T1.department_id  =  T2.department_id GROUP BY T1.department_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT D.department_name, D.department_id 
FROM Departments ...`
- **Multi_Agent** ✅: `SELECT d.department_name, d.department_id FROM Departments A...`
- **Multi_Agent_RAG** ✅: `SELECT d.department_name, d.department_id FROM Degree_Progra...`

### Q10 🟡
**What is the name and id of the department with the most number of degrees ?**
```sql
-- Gold: select t2.department_name ,  t1.department_id from degree_programs as t1 join departments as t2 on t1.department_id  =  t2.department_id group by t1.department_id order by count(*) desc limit 1
```
- **Single_Agent** ✅: `SELECT D.department_name, D.department_id 
FROM Departments ...`
- **Multi_Agent** ✅: `SELECT d.department_name, d.department_id FROM Departments A...`
- **Multi_Agent_RAG** ❌: `SELECT d.department_name, dp.degree_program_id FROM Degree_P...`

### Q11 🟢
**How many departments offer any degree?**
```sql
-- Gold: SELECT count(DISTINCT department_id) FROM Degree_Programs
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.department_id) 
FROM Departments AS...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT d.department_id) FROM Departments AS d...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT d.department_id) FROM Departments AS d...`

### Q12 🟢
**How many different departments offer degrees?**
```sql
-- Gold: SELECT count(DISTINCT department_id) FROM Degree_Programs
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.department_id) FROM Departments AS ...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT department_id) FROM Departments;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT T1.department_id) FROM Departments AS ...`

### Q13 🟢
**How many different degree names are offered?**
```sql
-- Gold: SELECT count(DISTINCT degree_summary_name) FROM Degree_Programs
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.degree_summary_name) 
FROM Degree_P...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Progr...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Progr...`

### Q14 🟢
**How many different degrees are offered?**
```sql
-- Gold: SELECT count(DISTINCT degree_summary_name) FROM Degree_Programs
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Progr...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT degree_summary_name) FROM Degree_Progr...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM Degree_Programs;...`

### Q15 🟡
**How many degrees does the engineering department offer?**
```sql
-- Gold: SELECT count(*) FROM Departments AS T1 JOIN Degree_Programs AS T2 ON T1.department_id  =  T2.department_id WHERE T1.department_name  =  'engineer'
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.degree_program_id) 
FROM Degree_Pro...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT T2.degree_program_id) FROM Departments...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Degree_Programs WHERE department_id = '...`

### Q16 🟡
**How many degrees does the engineering department have?**
```sql
-- Gold: SELECT count(*) FROM Departments AS T1 JOIN Degree_Programs AS T2 ON T1.department_id  =  T2.department_id WHERE T1.department_name  =  'engineer'
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.department_name) 
FROM Departments ...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT degree_program_id) FROM Degree_Program...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Degree_Programs WHERE department_id = '...`

### Q17 🟢
**What are the names and descriptions of all the sections?**
```sql
-- Gold: SELECT section_name ,  section_description FROM Sections
```
- **Single_Agent** ✅: `SELECT T1.section_name, T1.section_description 
FROM Section...`
- **Multi_Agent** ✅: `SELECT section_name, section_description FROM Sections;...`
- **Multi_Agent_RAG** ✅: `SELECT section_name, section_description FROM Sections;...`

### Q18 🟢
**What are the names and descriptions for all the sections?**
```sql
-- Gold: SELECT section_name ,  section_description FROM Sections
```
- **Single_Agent** ✅: `SELECT s.section_name, s.section_description 
FROM Sections ...`
- **Multi_Agent** ✅: `SELECT section_name, section_description FROM Sections;...`
- **Multi_Agent_RAG** ✅: `SELECT section_name, section_description FROM Sections;...`

### Q19 🟢
**List the section_name in reversed lexicographical order.**
```sql
-- Gold: SELECT section_name FROM Sections ORDER BY section_name DESC
```
- **Single_Agent** ❌: `SELECT DISTINCT T2.section_name FROM Student_Enrolment_Cours...`
- **Multi_Agent** ✅: `SELECT section_name FROM Sections ORDER BY section_name DESC...`
- **Multi_Agent_RAG** ✅: `SELECT section_name FROM Sections ORDER BY section_name DESC...`

### Q20 🟢
**What are the names of the sections in reverse alphabetical order?**
```sql
-- Gold: SELECT section_name FROM Sections ORDER BY section_name DESC
```
- **Single_Agent** ✅: `SELECT T1.section_name FROM Sections AS T1 INNER JOIN Course...`
- **Multi_Agent** ✅: `SELECT section_name FROM Sections ORDER BY section_name DESC...`
- **Multi_Agent_RAG** ❌: `SELECT section_name FROM Sections ORDER BY section_name ASC ...`

### Q21 🟡
**What is the semester which most student registered in? Show both the name and the id.**
```sql
-- Gold: SELECT T1.semester_name ,  T1.semester_id FROM Semesters AS T1 JOIN Student_Enrolment AS T2 ON T1.semester_id  =  T2.semester_id GROUP BY T1.semester_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT 
  s.semester_name,
  s.semester_id
FROM 
  Student_E...`
- **Multi_Agent** ❌: `SELECT s.semester_name, s.semester_id FROM Students AS s JOI...`
- **Multi_Agent_RAG** ✅: `SELECT s.semester_name, s.semester_id FROM Student_Enrolment...`

### Q22 🟡
**For each semester, what is the name and id of the one with the most students registered?**
```sql
-- Gold: SELECT T1.semester_name ,  T1.semester_id FROM Semesters AS T1 JOIN Student_Enrolment AS T2 ON T1.semester_id  =  T2.semester_id GROUP BY T1.semester_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT 
  s.semester_name,
  s.semester_id,
  COUNT(se.stude...`
- **Multi_Agent** ❌: `SELECT s.semester_name, s.semester_id FROM Students AS s JOI...`
- **Multi_Agent_RAG** ✅: `SELECT s.semester_name, s.semester_id FROM Semesters AS s JO...`

### Q23 🟢
**What is the description of the department whose name has the substring the computer?**
```sql
-- Gold: SELECT department_description FROM Departments WHERE department_name LIKE '%computer%'
```
- **Single_Agent** ❌: `SELECT T1.department_description 
FROM Departments AS T1 
JO...`
- **Multi_Agent** ✅: `SELECT d.department_description FROM Departments AS d WHERE ...`
- **Multi_Agent_RAG** ✅: `SELECT department_description FROM Departments WHERE departm...`

### Q24 🟢
**What is the department description for the one whose name has the word computer?**
```sql
-- Gold: SELECT department_description FROM Departments WHERE department_name LIKE '%computer%'
```
- **Single_Agent** ❌: `SELECT T2.department_description 
FROM Courses AS T1 
JOIN D...`
- **Multi_Agent** ❌: `SELECT T1.department_description FROM Departments AS T1 JOIN...`
- **Multi_Agent_RAG** ✅: `SELECT department_description FROM Departments WHERE departm...`

### Q25 🟡
**Find the kind of program which most number of students are enrolled in?**
```sql
-- Gold: SELECT T1.degree_summary_name FROM Degree_Programs AS T1 JOIN Student_Enrolment AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_summary_name ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT dp.degree_summary_name 
FROM Degree_Programs dp 
JOIN...`
- **Multi_Agent** ✅: `SELECT dp.degree_summary_name FROM Degree_Programs AS dp JOI...`
- **Multi_Agent_RAG** ❌: `SELECT p.degree_program_id, COUNT(p.degree_program_id) FROM ...`

### Q26 🟡
**What is the degree summary name that has the most number of students enrolled?**
```sql
-- Gold: SELECT T1.degree_summary_name FROM Degree_Programs AS T1 JOIN Student_Enrolment AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_summary_name ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT dp.degree_summary_name 
FROM Degree_Programs dp 
JOIN...`
- **Multi_Agent** ❌: `SELECT ds.degree_summary_name FROM Degree_Programs AS dp JOI...`
- **Multi_Agent_RAG** ✅: `SELECT c.degree_summary_name FROM Degree_Programs AS c JOIN ...`

### Q27 🟡
**Find the program which most number of students are enrolled in. List both the id and the summary.**
```sql
-- Gold: SELECT T1.degree_program_id ,  T1.degree_summary_name FROM Degree_Programs AS T1 JOIN Student_Enrolment AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_program_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT 
  dp.degree_program_id,
  dp.degree_summary_name AS ...`
- **Multi_Agent** ✅: `SELECT dp.degree_program_id, dp.degree_summary_name FROM Deg...`
- **Multi_Agent_RAG** ❌: `SELECT dp.degree_summary_name, COUNT(e.student_id) AS num_st...`

### Q28 🟡
**What is the program id and the summary of the degree that has the most students enrolled?**
```sql
-- Gold: SELECT T1.degree_program_id ,  T1.degree_summary_name FROM Degree_Programs AS T1 JOIN Student_Enrolment AS T2 ON T1.degree_program_id  =  T2.degree_program_id GROUP BY T1.degree_program_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT 
  dp.degree_program_id,
  dp.degree_summary_name,
  ...`
- **Multi_Agent** ✅: `SELECT T1.degree_program_id, T1.degree_summary_name FROM Deg...`
- **Multi_Agent_RAG** ✅: `SELECT dp.degree_program_id, dp.degree_summary_name FROM Deg...`

### Q29 🟡
**Which student has enrolled for the most times in any program? List the id, first name, middle name, last name, the number of enrollments and student id.**
```sql
-- Gold: SELECT T1.student_id ,  T1.first_name ,  T1.middle_name ,  T1.last_name ,  count(*) ,  T1.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id GROUP BY T1.student_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT 
  S.student_id,
  S.first_name,
  S.middle_name,
  S...`
- **Multi_Agent** ✅: `SELECT s.student_id, s.first_name, s.middle_name, s.last_nam...`
- **Multi_Agent_RAG** ✅: `SELECT s.first_name, s.middle_name, s.last_name, COUNT(se.de...`

### Q30 🟡
**What is the first, middle, and last name, along with the id and number of enrollments, for the student who enrolled the most in any program?**
```sql
-- Gold: SELECT T1.student_id ,  T1.first_name ,  T1.middle_name ,  T1.last_name ,  count(*) ,  T1.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id GROUP BY T1.student_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT 
  S.student_id,
  S.first_name,
  S.middle_name,
  S...`
- **Multi_Agent** ❌: `SELECT s.student_id, s.first_name, s.middle_name, s.last_nam...`
- **Multi_Agent_RAG** ❌: `SELECT s.student_id, s.first_name, s.middle_name, s.last_nam...`

### Q31 🟡
**What are all the course names of the courses which ever have students enrolled in?**
```sql
-- Gold: SELECT DISTINCT T1.course_name FROM Courses AS T1 JOIN Student_Enrolment_Courses AS T2 ON T1.course_id  =  T2.course_id
```
- **Single_Agent** ✅: `SELECT T1.course_name 
FROM Courses AS T1 
JOIN Student_Enro...`
- **Multi_Agent** ✅: `SELECT c.course_name FROM Courses AS c JOIN Student_Enrolmen...`
- **Multi_Agent_RAG** ✅: `SELECT c.course_name FROM Courses AS c JOIN Student_Enrolmen...`

### Q32 🟡
**What are the names of all courses that have some students enrolled?**
```sql
-- Gold: SELECT DISTINCT T1.course_name FROM Courses AS T1 JOIN Student_Enrolment_Courses AS T2 ON T1.course_id  =  T2.course_id
```
- **Single_Agent** ✅: `SELECT C.course_name 
FROM Courses C 
JOIN Student_Enrolment...`
- **Multi_Agent** ✅: `SELECT c.course_name FROM Courses AS c JOIN Student_Enrolmen...`
- **Multi_Agent_RAG** ✅: `SELECT c.course_name FROM Courses AS c JOIN Student_Enrolmen...`

### Q33 🟡
**What's the name of the course with most number of enrollments?**
```sql
-- Gold: SELECT  T1.course_name FROM Courses AS T1 JOIN Student_Enrolment_Courses AS T2 ON T1.course_id  =  T2.course_id GROUP BY T1.course_name ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT C.course_name 
FROM Student_Enrolment_Courses SEC 
JO...`
- **Multi_Agent** ✅: `SELECT c.course_name FROM Courses AS c JOIN Student_Enrolmen...`
- **Multi_Agent_RAG** ❌: `SELECT c.course_name FROM Student_Enrolment_Courses AS sec J...`

### Q34 🟡
**What is the name of the course with the most students enrolled?**
```sql
-- Gold: SELECT  T1.course_name FROM Courses AS T1 JOIN Student_Enrolment_Courses AS T2 ON T1.course_id  =  T2.course_id GROUP BY T1.course_name ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT C.course_name 
FROM Courses C 
JOIN Student_Enrolment...`
- **Multi_Agent** ✅: `SELECT c.course_name FROM Student_Enrolment_Courses AS sec J...`
- **Multi_Agent_RAG** ❌: `SELECT c.course_name FROM Courses AS c JOIN Student_Enrolmen...`

### Q35 🟢
**What is the phone number of the man with the first name Timmothy and the last name Ward?**
```sql
-- Gold: SELECT cell_mobile_number FROM Students WHERE first_name  =  'Timmothy' AND last_name  =  'Ward'
```
- **Single_Agent** ❌: `SELECT T1.cell_mobile_number 
FROM Students AS T1 
JOIN Stud...`
- **Multi_Agent** ✅: `SELECT cell_mobile_number FROM Students WHERE first_name = '...`
- **Multi_Agent_RAG** ✅: `SELECT cell_mobile_number FROM Students WHERE first_name = '...`

### Q36 🟢
**What is the mobile phone number of the student named Timmothy Ward ?**
```sql
-- Gold: select cell_mobile_number from students where first_name  =  'timmothy' and last_name  =  'ward'
```
- **Single_Agent** ❌: `SELECT T1.cell_mobile_number 
FROM Students AS T1 
JOIN Stud...`
- **Multi_Agent** ❌: `SELECT cell_mobile_number FROM Students WHERE first_name = '...`
- **Multi_Agent_RAG** ❌: `SELECT cell_mobile_number FROM Students WHERE first_name = '...`

### Q37 🟢
**Who is the first student to register? List the first name, middle name and last name.**
```sql
-- Gold: SELECT first_name ,  middle_name ,  last_name FROM Students ORDER BY date_first_registered ASC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.first_name, T1.middle_name, T1.last_name 
FROM Stu...`
- **Multi_Agent** ✅: `SELECT T1.first_name, T1.middle_name, T1.last_name FROM Stud...`
- **Multi_Agent_RAG** ✅: `SELECT first_name, middle_name, last_name FROM Students ORDE...`

### Q38 🟢
**What is the first, middle, and last name of the first student to register?**
```sql
-- Gold: SELECT first_name ,  middle_name ,  last_name FROM Students ORDER BY date_first_registered ASC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.first_name, T1.middle_name, T1.last_name FROM Stud...`
- **Multi_Agent** ✅: `SELECT first_name, middle_name, last_name FROM Students WHER...`
- **Multi_Agent_RAG** ✅: `SELECT first_name, middle_name, last_name FROM Students ORDE...`

### Q39 🟢
**Who is the earliest graduate of the school? List the first name, middle name and last name.**
```sql
-- Gold: SELECT first_name ,  middle_name ,  last_name FROM Students ORDER BY date_left ASC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.first_name, T1.middle_name, T1.last_name 
FROM Stu...`
- **Multi_Agent** ❌: `SELECT T1.first_name, T1.middle_name, T1.last_name FROM Stud...`
- **Multi_Agent_RAG** ❌: `SELECT T1.first_name, T1.middle_name, T1.last_name FROM Stud...`

### Q40 🟢
**What is the first, middle, and last name of the earliest school graduate?**
```sql
-- Gold: SELECT first_name ,  middle_name ,  last_name FROM Students ORDER BY date_left ASC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.first_name, T1.middle_name, T1.last_name 
FROM Stu...`
- **Multi_Agent** ❌: `SELECT T1.first_name, T1.middle_name, T1.last_name FROM Stud...`
- **Multi_Agent_RAG** ✅: `SELECT T1.first_name, T1.middle_name, T1.last_name FROM Stud...`

### Q41 🟢
**Whose permanent address is different from his or her current address? List his or her first name.**
```sql
-- Gold: SELECT first_name FROM Students WHERE current_address_id != permanent_address_id
```
- **Single_Agent** ✅: `SELECT DISTINCT T1.first_name 
FROM Students AS T1 
JOIN Add...`
- **Multi_Agent** ✅: `SELECT DISTINCT T1.first_name FROM Students AS T1 JOIN Addre...`
- **Multi_Agent_RAG** ✅: `SELECT DISTINCT S.first_name FROM Students AS S WHERE S.curr...`

### Q42 🟢
**What is the first name of the student whose permanent address is different from his or her current one?**
```sql
-- Gold: SELECT first_name FROM Students WHERE current_address_id != permanent_address_id
```
- **Single_Agent** ✅: `SELECT T1.first_name 
FROM Students AS T1 
JOIN Addresses AS...`
- **Multi_Agent** ✅: `SELECT T1.first_name FROM Students AS T1 JOIN Addresses AS T...`
- **Multi_Agent_RAG** ✅: `SELECT first_name FROM Students WHERE permanent_address_id <...`

### Q43 🟡
**Which address holds the most number of students currently? List the address id and all lines.**
```sql
-- Gold: SELECT T1.address_id ,  T1.line_1 ,  T1.line_2 FROM Addresses AS T1 JOIN Students AS T2 ON T1.address_id  =  T2.current_address_id GROUP BY T1.address_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT A.address_id, A.line_1, A.line_2, A.line_3
FROM Stude...`
- **Multi_Agent** ❌: `SELECT T1.line_1, T1.line_2, T1.line_3 FROM Addresses AS T1 ...`
- **Multi_Agent_RAG** ❌: `SELECT c.current_address_id, c.lines FROM Students AS s JOIN...`

### Q44 🟡
**What is the id, line 1, and line 2 of the address with the most students?**
```sql
-- Gold: SELECT T1.address_id ,  T1.line_1 ,  T1.line_2 FROM Addresses AS T1 JOIN Students AS T2 ON T1.address_id  =  T2.current_address_id GROUP BY T1.address_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT A.address_id, A.line_1, A.line_2
FROM Addresses A
JOI...`
- **Multi_Agent** ❌: `SELECT T1.address_id, T1.line_1, T1.line_2 FROM Addresses AS...`
- **Multi_Agent_RAG** ❌: `SELECT a.id, a.line_1, a.line_2 FROM Students AS s JOIN Addr...`

### Q45 🟢
**On average, when were the transcripts printed?**
```sql
-- Gold: SELECT avg(transcript_date) FROM Transcripts
```
- **Single_Agent** ✅: `SELECT AVG(transcript_date) FROM Transcripts...`
- **Multi_Agent** ✅: `SELECT AVG(transcript_date) FROM Transcripts;...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(transcript_date) FROM Transcripts;...`

### Q46 🟢
**What is the average transcript date?**
```sql
-- Gold: SELECT avg(transcript_date) FROM Transcripts
```
- **Single_Agent** ✅: `SELECT AVG(transcript_date) FROM Transcripts;...`
- **Multi_Agent** ✅: `SELECT AVG(transcript_date) FROM Transcripts;...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(transcript_date) FROM Transcripts;...`

### Q47 🟢
**When is the first transcript released? List the date and details.**
```sql
-- Gold: SELECT transcript_date ,  other_details FROM Transcripts ORDER BY transcript_date ASC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.transcript_date, T1.other_details FROM Transcripts...`
- **Multi_Agent** ❌: `SELECT T1.transcript_date, T1.other_details FROM Transcripts...`
- **Multi_Agent_RAG** ✅: `SELECT T.transcript_date, T.other_details FROM Transcripts A...`

### Q48 🟢
**What is the earliest date of a transcript release, and what details can you tell me?**
```sql
-- Gold: SELECT transcript_date ,  other_details FROM Transcripts ORDER BY transcript_date ASC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.transcript_date, 
       T1.other_details 
FROM Tr...`
- **Multi_Agent** ❌: `SELECT MIN(trancript_date) AS earliest_release_date, other_d...`
- **Multi_Agent_RAG** ✅: `SELECT T.transcript_date, T.other_details FROM Transcripts A...`

### Q49 🟢
**How many transcripts are released?**
```sql
-- Gold: SELECT count(*) FROM Transcripts
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM Transcripts WHERE transcript_date IS NO...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM Transcripts;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Transcripts;...`

### Q50 🟢
**How many transcripts are listed?**
```sql
-- Gold: SELECT count(*) FROM Transcripts
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM Transcripts...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM Transcripts;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Transcripts;...`

*... and 14 more questions*