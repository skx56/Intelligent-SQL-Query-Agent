# 🤖 Multi-Agent RAG Text-to-SQL Evaluation

**Database:** dog_kennels  
**Total Questions:** 46  
**Date:** 2025-12-21 20:50

---

## 📊 Summary - 3 Pipeline Comparison

| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |
|----------|-------------------|-----------------|-----------------|----------|
| **Single Agent** | 63.0% | 63.0% | 80.9% | 3.6s |
| **Multi Agent** | 71.7% | 71.7% | 83.9% | 10.7s |
| **Multi Agent RAG** | 82.6% | 82.6% | 85.7% | 17.9s |

### 🏆 Best: Multi Agent RAG (82.6%)

---

## 📈 Component Matching

| Pipeline | SELECT | FROM | WHERE | GROUP BY | ORDER BY |
|----------|--------|------|-------|----------|----------|
| Single Agent | 91% | 46% | 89% | 93% | 85% |
| Multi Agent | 91% | 72% | 85% | 87% | 85% |
| Multi Agent RAG | 87% | 89% | 80% | 91% | 80% |

---

## 📝 Detailed Results

### Q1 🟡
**Which owner owns the most dogs? List the owner id, first name and last name.**
```sql
-- Gold: SELECT T1.owner_id ,  T2.first_name ,  T2.last_name FROM Dogs AS T1 JOIN Owners AS T2 ON T1.owner_id  =  T2.owner_id GROUP BY T1.owner_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT o.owner_id, o.first_name, o.last_name 
FROM Owners o ...`
- **Multi_Agent** ✅: `SELECT o.owner_id, o.first_name, o.last_name FROM Dogs AS d ...`
- **Multi_Agent_RAG** ✅: `SELECT o.owner_id, o.first_name, o.last_name FROM Owners AS ...`

### Q2 🟡
**Return the owner id, first name and last name of the owner who has the most dogs.**
```sql
-- Gold: SELECT T1.owner_id ,  T2.first_name ,  T2.last_name FROM Dogs AS T1 JOIN Owners AS T2 ON T1.owner_id  =  T2.owner_id GROUP BY T1.owner_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT o.owner_id, o.first_name, o.last_name 
FROM Owners o ...`
- **Multi_Agent** ✅: `SELECT o.owner_id, o.first_name, o.last_name FROM Owners AS ...`
- **Multi_Agent_RAG** ✅: `SELECT o.owner_id, o.first_name, o.last_name FROM Owners AS ...`

### Q3 🟡
**What is the name of the breed with the most dogs?**
```sql
-- Gold: SELECT T1.breed_name FROM Breeds AS T1 JOIN Dogs AS T2 ON T1.breed_code  =  T2.breed_code GROUP BY T1.breed_name ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.breed_name 
FROM Breeds AS T1 
JOIN Dogs AS T2 ON ...`
- **Multi_Agent** ❌: `SELECT breed_name FROM Dogs GROUP BY breed_code ORDER BY COU...`
- **Multi_Agent_RAG** ✅: `SELECT b.breed_name FROM Dogs AS d JOIN Breeds AS b ON d.bre...`

### Q4 🟡
**Which breed do the most dogs have? Give me the breed name.**
```sql
-- Gold: SELECT T1.breed_name FROM Breeds AS T1 JOIN Dogs AS T2 ON T1.breed_code  =  T2.breed_code GROUP BY T1.breed_name ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.breed_name 
FROM Breeds AS T1 
JOIN Dogs AS T2 ON ...`
- **Multi_Agent** ✅: `SELECT b.breed_name FROM Dogs AS d JOIN Breeds AS b ON d.bre...`
- **Multi_Agent_RAG** ✅: `SELECT b.breed_name FROM Dogs AS d JOIN Breeds AS b ON d.bre...`

### Q5 🟡
**What is the description of the treatment type that costs the least money in total?**
```sql
-- Gold: SELECT T1.treatment_type_description FROM Treatment_types AS T1 JOIN Treatments AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code GROUP BY T1.treatment_type_code ORDER BY sum(cost_of_treatment) ASC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.treatment_type_description 
FROM Treatment_Types A...`
- **Multi_Agent** ✅: `SELECT tt.treatment_type_description FROM Treatments AS t JO...`
- **Multi_Agent_RAG** ✅: `SELECT tt.treatment_type_description FROM Treatment_Types AS...`

### Q6 🟡
**Give me the description of the treatment type whose total cost is the lowest.**
```sql
-- Gold: SELECT T1.treatment_type_description FROM Treatment_types AS T1 JOIN Treatments AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code GROUP BY T1.treatment_type_code ORDER BY sum(cost_of_treatment) ASC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.treatment_type_description 
FROM Treatment_Types A...`
- **Multi_Agent** ✅: `SELECT tt.treatment_type_description FROM Treatments AS t JO...`
- **Multi_Agent_RAG** ✅: `SELECT tt.treatment_type_description FROM Treatments AS t JO...`

### Q7 🟡
**List the date of each treatment, together with the first name of the professional who operated it.**
```sql
-- Gold: SELECT T1.date_of_treatment ,  T2.first_name FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id
```
- **Single_Agent** ✅: `SELECT T1.date_of_treatment, P.first_name 
FROM Treatments T...`
- **Multi_Agent** ✅: `SELECT T1.date_of_treatment, T2.first_name FROM Treatments A...`
- **Multi_Agent_RAG** ✅: `SELECT T.date_of_treatment, P.first_name FROM Treatments AS ...`

### Q8 🟡
**What are the date and the operating professional's first name of each treatment?**
```sql
-- Gold: SELECT T1.date_of_treatment ,  T2.first_name FROM Treatments AS T1 JOIN Professionals AS T2 ON T1.professional_id  =  T2.professional_id
```
- **Single_Agent** ✅: `SELECT T.date_of_treatment, P.first_name 
FROM Treatments T ...`
- **Multi_Agent** ✅: `SELECT T1.date_of_treatment, P.first_name FROM Treatments AS...`
- **Multi_Agent_RAG** ❌: `SELECT T.date_of_treatment, OP.first_name FROM Treatments AS...`

### Q9 🟡
**List the cost of each treatment and the corresponding treatment type description.**
```sql
-- Gold: SELECT T1.cost_of_treatment ,  T2.treatment_type_description FROM Treatments AS T1 JOIN treatment_types AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code
```
- **Single_Agent** ❌: `SELECT T.treatment_type_description, T.cost_of_treatment 
FR...`
- **Multi_Agent** ✅: `SELECT t.cost_of_treatment, tt.treatment_type_description FR...`
- **Multi_Agent_RAG** ✅: `SELECT t.cost_of_treatment, tt.treatment_type_description FR...`

### Q10 🟡
**What are the cost and treatment type description of each treatment?**
```sql
-- Gold: SELECT T1.cost_of_treatment ,  T2.treatment_type_description FROM Treatments AS T1 JOIN treatment_types AS T2 ON T1.treatment_type_code  =  T2.treatment_type_code
```
- **Single_Agent** ✅: `SELECT 
  t.cost_of_treatment,
  tt.treatment_type_descripti...`
- **Multi_Agent** ✅: `SELECT t.cost_of_treatment, tt.treatment_type_description FR...`
- **Multi_Agent_RAG** ✅: `SELECT t.cost_of_treatment, tt.treatment_type_description FR...`

### Q11 🟡
**List each owner's first name, last name, and the size of his for her dog.**
```sql
-- Gold: SELECT T1.first_name ,  T1.last_name ,  T2.size_code FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id  =  T2.owner_id
```
- **Single_Agent** ❌: `SELECT 
  o.first_name,
  o.last_name,
  s.size_description
...`
- **Multi_Agent** ✅: `SELECT o.first_name, o.last_name, d.size_code FROM Owners AS...`
- **Multi_Agent_RAG** ✅: `SELECT o.first_name, o.last_name, d.size_code FROM owners AS...`

### Q12 🟡
**What are each owner's first name, last name, and the size of their dog?**
```sql
-- Gold: SELECT T1.first_name ,  T1.last_name ,  T2.size_code FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id  =  T2.owner_id
```
- **Single_Agent** ✅: `SELECT 
  o.first_name,
  o.last_name,
  d.size_code
FROM 
 ...`
- **Multi_Agent** ✅: `SELECT o.first_name, o.last_name, d.size_code FROM Owners AS...`
- **Multi_Agent_RAG** ✅: `SELECT o.first_name, o.last_name, d.size_code FROM Owners AS...`

### Q13 🟡
**List pairs of the owner's first name and the dogs's name.**
```sql
-- Gold: SELECT T1.first_name ,  T2.name FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id  =  T2.owner_id
```
- **Single_Agent** ✅: `SELECT o.first_name, d.name 
FROM Owners o 
JOIN Dogs d ON o...`
- **Multi_Agent** ✅: `SELECT o.first_name, d.name FROM Owners AS o JOIN Dogs AS d ...`
- **Multi_Agent_RAG** ✅: `SELECT o.first_name, d.name FROM Owners AS o JOIN Dogs AS d ...`

### Q14 🟡
**What are each owner's first name and their dogs's name?**
```sql
-- Gold: SELECT T1.first_name ,  T2.name FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id  =  T2.owner_id
```
- **Single_Agent** ✅: `SELECT o.first_name, d.name 
FROM Owners o 
JOIN Dogs d ON o...`
- **Multi_Agent** ✅: `SELECT o.first_name, d.name FROM Owners AS o JOIN Dogs AS d ...`
- **Multi_Agent_RAG** ✅: `SELECT o.first_name, d.name FROM Owners AS o JOIN Dogs AS d ...`

### Q15 🟡
**Which dogs are owned by someone who lives in Virginia? List the owner's first name and the dog's name.**
```sql
-- Gold: SELECT T1.first_name ,  T2.name FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id  =  T2.owner_id WHERE T1.state  =  'Virginia'
```
- **Single_Agent** ❌: `SELECT T1.first_name, T1.name 
FROM Owners AS T1 
JOIN Dogs ...`
- **Multi_Agent** ✅: `SELECT o.first_name, d.name FROM Owners AS o JOIN Dogs AS d ...`
- **Multi_Agent_RAG** ❌: `SELECT o.first_name, d.name FROM Dogs AS d JOIN Owners AS o ...`

### Q16 🟡
**Find the first names of owners living in Virginia and the names of dogs they own.**
```sql
-- Gold: SELECT T1.first_name ,  T2.name FROM Owners AS T1 JOIN Dogs AS T2 ON T1.owner_id  =  T2.owner_id WHERE T1.state  =  'Virginia'
```
- **Single_Agent** ✅: `SELECT DISTINCT o.first_name, d.name 
FROM Owners o 
JOIN Do...`
- **Multi_Agent** ❌: `SELECT o.first_name FROM owners AS o JOIN dogs AS d ON o.own...`
- **Multi_Agent_RAG** ✅: `SELECT o.first_name, d.name FROM Owners AS o JOIN Dogs AS d ...`

### Q17 🟡
**What are the arriving date and the departing date of the dogs who have gone through a treatment?**
```sql
-- Gold: SELECT DISTINCT T1.date_arrived ,  T1.date_departed FROM Dogs AS T1 JOIN Treatments AS T2 ON T1.dog_id  =  T2.dog_id
```
- **Single_Agent** ❌: `SELECT D.date_arrived, D.date_departed 
FROM Dogs D 
JOIN Tr...`
- **Multi_Agent** ✅: `SELECT T1.date_arrived, T1.date_departed FROM Dogs AS T1 JOI...`
- **Multi_Agent_RAG** ✅: `SELECT d.date_arrived, d.date_departed FROM Dogs AS d JOIN T...`

### Q18 🟡
**Find the arriving date and the departing date of the dogs that received a treatment.**
```sql
-- Gold: SELECT DISTINCT T1.date_arrived ,  T1.date_departed FROM Dogs AS T1 JOIN Treatments AS T2 ON T1.dog_id  =  T2.dog_id
```
- **Single_Agent** ✅: `SELECT 
  d.date_arrived,
  d.date_departed
FROM 
  Dogs d
J...`
- **Multi_Agent** ✅: `SELECT T1.date_arrived, T1.date_departed FROM Dogs AS T1 JOI...`
- **Multi_Agent_RAG** ✅: `SELECT T1.date_arrived, T1.date_departed FROM Dogs AS T1 JOI...`

### Q19 🟢
**List the emails of the professionals who live in the state of Hawaii or the state of Wisconsin.**
```sql
-- Gold: SELECT email_address FROM Professionals WHERE state  =  'Hawaii' OR state  =  'Wisconsin'
```
- **Single_Agent** ❌: `SELECT DISTINCT T1.email_address 
FROM Professionals AS T1 
...`
- **Multi_Agent** ❌: `SELECT p.email_address FROM Professionals AS p JOIN States A...`
- **Multi_Agent_RAG** ❌: `SELECT T1.email_address FROM Professionals AS T1 JOIN States...`

### Q20 🟢
**What are the emails of the professionals living in either the state of Hawaii or the state of Wisconsin?**
```sql
-- Gold: SELECT email_address FROM Professionals WHERE state  =  'Hawaii' OR state  =  'Wisconsin'
```
- **Single_Agent** ❌: `SELECT DISTINCT T1.email_address 
FROM Professionals AS T1 
...`
- **Multi_Agent** ❌: `SELECT T1.email_address FROM Professionals AS T1 JOIN States...`
- **Multi_Agent_RAG** ✅: `SELECT email_address FROM Professionals WHERE state = 'Hawai...`

### Q21 🟢
**What are the arriving date and the departing date of all the dogs?**
```sql
-- Gold: SELECT date_arrived ,  date_departed FROM Dogs
```
- **Single_Agent** ✅: `SELECT 
  D.date_arrived,
  D.date_departed
FROM 
  Dogs D
W...`
- **Multi_Agent** ✅: `SELECT T1.date_arrived, T1.date_departed FROM Dogs AS T1;...`
- **Multi_Agent_RAG** ✅: `SELECT date_arrived, date_departed FROM Dogs;...`

### Q22 🟢
**List the arrival date and the departure date for all the dogs.**
```sql
-- Gold: SELECT date_arrived ,  date_departed FROM Dogs
```
- **Single_Agent** ❌: `SELECT T1.date_arrived, T1.date_departed FROM Dogs AS T1 INN...`
- **Multi_Agent** ✅: `SELECT T1.date_arrived, T1.date_departed FROM Dogs AS T1;...`
- **Multi_Agent_RAG** ✅: `SELECT date_arrived, date_departed FROM Dogs;...`

### Q23 🟢
**How many dogs went through any treatments?**
```sql
-- Gold: SELECT count(DISTINCT dog_id) FROM Treatments
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.dog_id) FROM Treatments AS T1 INNER...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT t.treatment_id) FROM Treatments AS t J...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM Treatments;...`

### Q24 🟢
**Count the number of dogs that went through a treatment.**
```sql
-- Gold: SELECT count(DISTINCT dog_id) FROM Treatments
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT t.treatment_id) 
FROM Treatments t 
JO...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM Dogs JOIN Treatments ON Dogs.dog_id = T...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM Treatments;...`

### Q25 🟢
**How many professionals have performed any treatment to dogs?**
```sql
-- Gold: SELECT count(DISTINCT professional_id) FROM Treatments
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT p.professional_id)
FROM Professionals ...`
- **Multi_Agent** ❌: `...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT professional_id) FROM Treatments WHERE...`

### Q26 🟢
**Find the number of professionals who have ever treated dogs.**
```sql
-- Gold: SELECT count(DISTINCT professional_id) FROM Treatments
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT professional_id) 
FROM Treatments t
JO...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT professional_id) FROM Treatments;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT professional_id) FROM Treatments;...`

### Q27 🟢
**Which professionals live in a city containing the substring 'West'? List his or her role, street, city and state.**
```sql
-- Gold: SELECT role_code ,  street ,  city ,  state FROM professionals WHERE city LIKE '%West%'
```
- **Single_Agent** ❌: `SELECT P.role_code, P.street, O.city, O.state 
FROM Professi...`
- **Multi_Agent** ❌: `SELECT p.role_code, p.street, c.city, c.state FROM Professio...`
- **Multi_Agent_RAG** ✅: `SELECT DISTINCT c.role_code, c.street, c.city, c.state FROM ...`

### Q28 🟢
**Find the role, street, city and state of the professionals living in a city that contains the substring 'West'.**
```sql
-- Gold: SELECT role_code ,  street ,  city ,  state FROM professionals WHERE city LIKE '%West%'
```
- **Single_Agent** ❌: `SELECT p.role_code, p.street, p.city, p.state 
FROM Professi...`
- **Multi_Agent** ❌: `SELECT p.role_code, p.street, c.city, c.state FROM Professio...`
- **Multi_Agent_RAG** ✅: `SELECT c.role_code, c.street, c.city, c.state FROM Professio...`

### Q29 🟢
**Which owners live in the state whose name contains the substring 'North'? List his first name, last name and email.**
```sql
-- Gold: SELECT first_name ,  last_name ,  email_address FROM Owners WHERE state LIKE '%North%'
```
- **Single_Agent** ✅: `SELECT 
  o.first_name,
  o.last_name,
  o.email_address
FRO...`
- **Multi_Agent** ❌: `SELECT o.first_name, o.last_name, o.email_address FROM Owner...`
- **Multi_Agent_RAG** ❌: `SELECT o.first_name, o.last_name, o.email_address FROM Owner...`

### Q30 🟢
**Return the first name, last name and email of the owners living in a state whose name contains the substring 'North'.**
```sql
-- Gold: SELECT first_name ,  last_name ,  email_address FROM Owners WHERE state LIKE '%North%'
```
- **Single_Agent** ❌: `SELECT o.first_name, o.last_name, o.email_address 
FROM Owne...`
- **Multi_Agent** ✅: `SELECT o.first_name, o.last_name, o.email_address FROM Owner...`
- **Multi_Agent_RAG** ❌: `SELECT first_name, last_name, email_address FROM Owners WHER...`

### Q31 🟢
**How much does the most recent treatment cost?**
```sql
-- Gold: SELECT cost_of_treatment FROM Treatments ORDER BY date_of_treatment DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.cost_of_treatment FROM Treatments AS T1 INNER JOIN...`
- **Multi_Agent** ❌: `SELECT MAX(TREATMENT_ID) * cost_of_treatment FROM Treatments...`
- **Multi_Agent_RAG** ✅: `SELECT MAX(cost_of_treatment) FROM Treatments WHERE date_of_...`

### Q32 🟢
**Show me the cost of the most recently performed treatment.**
```sql
-- Gold: SELECT cost_of_treatment FROM Treatments ORDER BY date_of_treatment DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.cost_of_treatment FROM Treatments AS T1 INNER JOIN...`
- **Multi_Agent** ✅: `SELECT T1.cost_of_treatment FROM Treatments AS T1 JOIN Dogs ...`
- **Multi_Agent_RAG** ✅: `SELECT MAX(cost_of_treatment) FROM Treatments WHERE date_of_...`

### Q33 🟢
**List the dog name, age and weight of the dogs who have been abandoned? 1 stands for yes, and 0 stands for no.**
```sql
-- Gold: SELECT name ,  age ,  weight FROM Dogs WHERE abandoned_yn  =  1
```
- **Single_Agent** ✅: `SELECT T1.name, T1.age, T1.weight 
FROM Dogs AS T1 
JOIN Own...`
- **Multi_Agent** ✅: `SELECT T1.name, T1.age, T1.weight FROM Dogs AS T1 INNER JOIN...`
- **Multi_Agent_RAG** ✅: `SELECT name, age, weight FROM Dogs WHERE abandoned_yn = '1';...`

### Q34 🟢
**What are the dog name, age and weight of the dogs that were abandoned? Note that 1 stands for yes, and 0 stands for no in the tables.**
```sql
-- Gold: SELECT name ,  age ,  weight FROM Dogs WHERE abandoned_yn  =  1
```
- **Single_Agent** ✅: `SELECT T1.name, T1.age, T1.weight 
FROM Dogs AS T1 
JOIN Own...`
- **Multi_Agent** ✅: `SELECT D.name, D.age, D.weight FROM Dogs AS D WHERE D.abando...`
- **Multi_Agent_RAG** ✅: `SELECT name, age, weight FROM Dogs WHERE abandoned_yn = '1';...`

### Q35 🟢
**What is the average age of all the dogs?**
```sql
-- Gold: SELECT avg(age) FROM Dogs
```
- **Single_Agent** ✅: `SELECT AVG(T1.age) FROM Dogs AS T1 INNER JOIN Owners AS T2 O...`
- **Multi_Agent** ✅: `SELECT AVG(age) FROM Dogs;...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(age) FROM Dogs;...`

### Q36 🟢
**Compute the average age of all the dogs.**
```sql
-- Gold: SELECT avg(age) FROM Dogs
```
- **Single_Agent** ✅: `SELECT AVG(T1.age) FROM Dogs AS T1 INNER JOIN Owners AS T2 O...`
- **Multi_Agent** ✅: `SELECT AVG(age) FROM Dogs;...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(age) FROM Dogs;...`

### Q37 🟢
**What is the age of the oldest dog?**
```sql
-- Gold: SELECT max(age) FROM Dogs
```
- **Single_Agent** ✅: `SELECT MAX(T1.age) FROM Dogs AS T1 INNER JOIN Owners AS T2 O...`
- **Multi_Agent** ✅: `SELECT MAX(age) FROM Dogs;...`
- **Multi_Agent_RAG** ✅: `SELECT MAX(age) FROM Dogs;...`

### Q38 🟢
**Tell me the age of the oldest dog.**
```sql
-- Gold: SELECT max(age) FROM Dogs
```
- **Single_Agent** ✅: `SELECT MAX(T1.age) FROM Dogs AS T1 INNER JOIN Owners AS T2 O...`
- **Multi_Agent** ✅: `SELECT MAX(age) FROM Dogs;...`
- **Multi_Agent_RAG** ✅: `SELECT MAX(age) FROM Dogs;...`

### Q39 🟢
**How much does each charge type costs? List both charge type and amount.**
```sql
-- Gold: SELECT charge_type ,  charge_amount FROM Charges
```
- **Single_Agent** ✅: `SELECT 
  c.charge_type,
  SUM(c.charge_amount) AS total_cos...`
- **Multi_Agent** ✅: `SELECT charge_type, charge_amount FROM Charges;...`
- **Multi_Agent_RAG** ✅: `SELECT charge_type, SUM(charge_amount) FROM Charges GROUP BY...`

### Q40 🟢
**List each charge type and its amount.**
```sql
-- Gold: SELECT charge_type ,  charge_amount FROM Charges
```
- **Single_Agent** ❌: `SELECT DISTINCT T1.charge_type, T1.charge_amount 
FROM Charg...`
- **Multi_Agent** ✅: `SELECT charge_type, charge_amount FROM Charges;...`
- **Multi_Agent_RAG** ✅: `SELECT charge_type, charge_amount FROM Charges;...`

### Q41 🟢
**How much does the most expensive charge type costs?**
```sql
-- Gold: SELECT max(charge_amount) FROM Charges
```
- **Single_Agent** ❌: `SELECT T1.charge_amount FROM Charges AS T1 INNER JOIN Treatm...`
- **Multi_Agent** ✅: `SELECT MAX(charge_amount) FROM Charges;...`
- **Multi_Agent_RAG** ✅: `SELECT MAX(charge_amount) FROM Charges;...`

### Q42 🟢
**What is the charge amount of the most expensive charge type?**
```sql
-- Gold: SELECT max(charge_amount) FROM Charges
```
- **Single_Agent** ❌: `SELECT T1.charge_amount 
FROM Charges AS T1 
JOIN (
  SELECT...`
- **Multi_Agent** ✅: `SELECT MAX(charge_amount) FROM Charges;...`
- **Multi_Agent_RAG** ✅: `SELECT charge_amount FROM Charges ORDER BY charge_amount DES...`

### Q43 🟢
**List the email, cell phone and home phone of all the professionals.**
```sql
-- Gold: SELECT email_address ,  cell_number ,  home_phone FROM professionals
```
- **Single_Agent** ✅: `SELECT 
  p.email_address,
  p.cell_number,
  p.home_phone
F...`
- **Multi_Agent** ✅: `SELECT p.email_address, p.cell_number, p.home_phone FROM Pro...`
- **Multi_Agent_RAG** ✅: `SELECT email_address, cell_number, home_phone FROM Professio...`

### Q44 🟢
**What are the email, cell phone and home phone of each professional?**
```sql
-- Gold: SELECT email_address ,  cell_number ,  home_phone FROM professionals
```
- **Single_Agent** ✅: `SELECT 
  p.email_address,
  p.cell_number,
  p.home_phone
F...`
- **Multi_Agent** ❌: `SELECT ci.email_address, ci.cell_number, ci.home_phone FROM ...`
- **Multi_Agent_RAG** ✅: `SELECT email_address, cell_number, home_phone FROM Professio...`

### Q45 🟢
**What are all the possible breed type and size type combinations?**
```sql
-- Gold: SELECT DISTINCT breed_code ,  size_code FROM dogs
```
- **Single_Agent** ❌: `SELECT DISTINCT T1.breed_name, T2.size_description 
FROM Bre...`
- **Multi_Agent** ✅: `SELECT breed_code, size_code FROM Dogs GROUP BY breed_code, ...`
- **Multi_Agent_RAG** ❌: `SELECT breed_code, size_code FROM Breeds;...`

### Q46 🟢
**Find the distinct breed type and size type combinations for dogs.**
```sql
-- Gold: SELECT DISTINCT breed_code ,  size_code FROM dogs
```
- **Single_Agent** ❌: `SELECT DISTINCT T1.breed_name, T1.size_description 
FROM Bre...`
- **Multi_Agent** ❌: `SELECT DISTINCT bt.breed_type, st.size_type FROM Dogs AS d J...`
- **Multi_Agent_RAG** ✅: `SELECT DISTINCT breed_code, size_code FROM Dogs;...`
