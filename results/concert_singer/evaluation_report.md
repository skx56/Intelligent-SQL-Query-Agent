# 🤖 Multi-Agent RAG Text-to-SQL Evaluation

**Database:** concert_singer  
**Total Questions:** 32  
**Date:** 2025-12-21 19:51

---

## 📊 Summary - 3 Pipeline Comparison

| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |
|----------|-------------------|-----------------|-----------------|----------|
| **Single Agent** | 56.2% | 56.2% | 75.6% | 2.6s |
| **Multi Agent** | 59.4% | 59.4% | 78.1% | 9.4s |
| **Multi Agent RAG** | 56.2% | 56.2% | 82.5% | 23.8s |

### 🏆 Best: Multi Agent (59.4%)

---

## 📈 Component Matching

| Pipeline | SELECT | FROM | WHERE | GROUP BY | ORDER BY |
|----------|--------|------|-------|----------|----------|
| Single Agent | 84% | 56% | 84% | 78% | 75% |
| Multi Agent | 88% | 59% | 84% | 75% | 84% |
| Multi Agent RAG | 84% | 72% | 88% | 88% | 81% |

---

## 📝 Detailed Results

### Q1 🟢
**How many singers do we have?**
```sql
-- Gold: SELECT count(*) FROM singer
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT Singer_ID) FROM singer...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM singer;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM singer;...`

### Q2 🟢
**What is the total number of singers?**
```sql
-- Gold: SELECT count(*) FROM singer
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM singer...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM singer;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM singer;...`

### Q3 🟢
**Show name, country, age for all singers ordered by age from the oldest to the youngest.**
```sql
-- Gold: SELECT name ,  country ,  age FROM singer ORDER BY age DESC
```
- **Single_Agent** ✅: `SELECT T1.Name, T1.Country, T1.Age 
FROM singer AS T1 
ORDER...`
- **Multi_Agent** ✅: `SELECT s.Name, s.Country, s.Age FROM singer AS s ORDER BY s....`
- **Multi_Agent_RAG** ✅: `SELECT s.Name, s.Country, s.Age FROM singer AS s ORDER BY s....`

### Q4 🟢
**What are the names, countries, and ages for every singer in descending order of age?**
```sql
-- Gold: SELECT name ,  country ,  age FROM singer ORDER BY age DESC
```
- **Single_Agent** ❌: `SELECT T1.Name, T1.Country, T1.Age FROM singer AS T1 INNER J...`
- **Multi_Agent** ❌: `SELECT s.Name, c.Country, s.Age FROM singer AS s JOIN countr...`
- **Multi_Agent_RAG** ✅: `SELECT Name, Country, Age FROM singer ORDER BY Age DESC;...`

### Q5 🟢
**What is the average, minimum, and maximum age of all singers from France?**
```sql
-- Gold: SELECT avg(age) ,  min(age) ,  max(age) FROM singer WHERE country  =  'France'
```
- **Single_Agent** ❌: `SELECT AVG(T1.Age), MIN(T1.Age), MAX(T1.Age) 
FROM singer AS...`
- **Multi_Agent** ✅: `SELECT AVG(Age), MIN(Age), MAX(Age) FROM singer WHERE Countr...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(Age) FROM singer WHERE Country = 'France' ORDER B...`

### Q6 🟢
**What is the average, minimum, and maximum age for all French singers?**
```sql
-- Gold: SELECT avg(age) ,  min(age) ,  max(age) FROM singer WHERE country  =  'France'
```
- **Single_Agent** ❌: `SELECT AVG(T1.Age), MIN(T1.Age), MAX(T1.Age) 
FROM singer AS...`
- **Multi_Agent** ✅: `SELECT AVG(Age), MIN(Age), MAX(Age) FROM singer WHERE Countr...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(Age), MIN(Age), MAX(Age) FROM singer WHERE Countr...`

### Q7 🟢
**Show the name and the release year of the song by the youngest singer.**
```sql
-- Gold: SELECT song_name ,  song_release_year FROM singer ORDER BY age LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Name, T1.Song_release_year 
FROM singer AS T1 
JOI...`
- **Multi_Agent** ❌: `SELECT s.Name, s.Song_Name, s.Song_release_year FROM singer ...`
- **Multi_Agent_RAG** ❌: `SELECT s.Name, s.Song_Name, s.Song_release_year FROM singer ...`

### Q8 🟢
**What are the names and release years for all the songs of the youngest singer?**
```sql
-- Gold: SELECT song_name ,  song_release_year FROM singer ORDER BY age LIMIT 1
```
- **Single_Agent** ✅: `SELECT s.Song_Name, s.Song_release_year 
FROM singer_in_conc...`
- **Multi_Agent** ✅: `SELECT s.Song_Name, s.Song_release_year FROM singer AS s JOI...`
- **Multi_Agent_RAG** ✅: `SELECT s.Song_Name, s.Song_release_year FROM singer AS s JOI...`

### Q9 🟢
**What are all distinct countries where singers above age 20 are from?**
```sql
-- Gold: SELECT DISTINCT country FROM singer WHERE age  >  20
```
- **Single_Agent** ❌: `SELECT DISTINCT T2.Country FROM singer AS T1 INNER JOIN sing...`
- **Multi_Agent** ❌: `SELECT DISTINCT c.Name FROM singer AS s JOIN country AS c ON...`
- **Multi_Agent_RAG** ❌: `SELECT DISTINCT c.Name FROM singer AS s JOIN singer_in_conce...`

### Q10 🟢
**What are  the different countries with singers above age 20?**
```sql
-- Gold: SELECT DISTINCT country FROM singer WHERE age  >  20
```
- **Single_Agent** ❌: `SELECT DISTINCT T1.Country 
FROM singer AS T1 
JOIN singer_i...`
- **Multi_Agent** ❌: `SELECT DISTINCT c.Name FROM singer AS s JOIN country AS c ON...`
- **Multi_Agent_RAG** ❌: `SELECT DISTINCT c.Name FROM singer AS s JOIN country AS c ON...`

### Q11 🟡
**Show all countries and the number of singers in each country.**
```sql
-- Gold: SELECT country ,  count(*) FROM singer GROUP BY country
```
- **Single_Agent** ✅: `SELECT s.Country, COUNT(s.Singer_ID) AS Singer_Count
FROM si...`
- **Multi_Agent** ❌: `SELECT c.Name, COUNT(s.Singer_ID) FROM country AS c JOIN sin...`
- **Multi_Agent_RAG** ❌: `SELECT c.Name, COUNT(DISTINCT si.Singer_ID) FROM country AS ...`

### Q12 🟡
**How many singers are from each country?**
```sql
-- Gold: SELECT country ,  count(*) FROM singer GROUP BY country
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT Singer_ID) AS num_singers, Country 
FR...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT c.Country) FROM singer AS s JOIN count...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(DISTINCT c.Country) FROM singer AS s JOIN count...`

### Q13 🟢
**Show location and name for all stadiums with a capacity between 5000 and 10000.**
```sql
-- Gold: SELECT LOCATION ,  name FROM stadium WHERE capacity BETWEEN 5000 AND 10000
```
- **Single_Agent** ✅: `SELECT T1.Location, T1.Name 
FROM stadium AS T1 
JOIN concer...`
- **Multi_Agent** ✅: `SELECT Location, Name FROM stadium WHERE Capacity BETWEEN 50...`
- **Multi_Agent_RAG** ✅: `SELECT Location, Name FROM stadium WHERE Capacity BETWEEN 50...`

### Q14 🟢
**What are the locations and names of all stations with capacity between 5000 and 10000?**
```sql
-- Gold: SELECT LOCATION ,  name FROM stadium WHERE capacity BETWEEN 5000 AND 10000
```
- **Single_Agent** ✅: `SELECT T1.Location, T1.Name 
FROM stadium AS T1 
JOIN concer...`
- **Multi_Agent** ❌: `SELECT Location, Name FROM station WHERE Capacity BETWEEN 50...`
- **Multi_Agent_RAG** ❌: `SELECT Location, Name FROM station WHERE Capacity BETWEEN 50...`

### Q15 🟢
**What is the maximum capacity and the average of all stadiums ?**
```sql
-- Gold: select max(capacity), average from stadium
```
- **Single_Agent** ❌: `SELECT MAX(Capacity), AVG(Average) FROM stadium...`
- **Multi_Agent** ❌: `SELECT MAX(Capacity), AVG(Average) FROM stadium;...`
- **Multi_Agent_RAG** ❌: `SELECT MAX(Capacity), AVG(Average) FROM stadium;...`

### Q16 🟢
**What is the average and maximum capacities for all stadiums ?**
```sql
-- Gold: select avg(capacity) ,  max(capacity) from stadium
```
- **Single_Agent** ✅: `SELECT AVG(Capacity) ,  MAX(Capacity) FROM stadium...`
- **Multi_Agent** ✅: `SELECT AVG(Capacity) AS AverageCapacity, MAX(Capacity) FROM ...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(Capacity) AS AverageCapacity, MAX(Capacity) FROM ...`

### Q17 🟢
**What is the name and capacity for the stadium with highest average attendance?**
```sql
-- Gold: SELECT name ,  capacity FROM stadium ORDER BY average DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.Name, T1.Capacity 
FROM stadium AS T1 
JOIN (
  SE...`
- **Multi_Agent** ✅: `SELECT Name, Capacity FROM stadium WHERE Average = (SELECT M...`
- **Multi_Agent_RAG** ✅: `SELECT Name, Capacity FROM stadium WHERE Average = (SELECT M...`

### Q18 🟢
**What is the name and capacity for the stadium with the highest average attendance?**
```sql
-- Gold: SELECT name ,  capacity FROM stadium ORDER BY average DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT s.Name, s.Capacity 
FROM stadium s 
JOIN (
  SELECT S...`
- **Multi_Agent** ✅: `SELECT Name, Capacity FROM stadium WHERE Average = (SELECT M...`
- **Multi_Agent_RAG** ✅: `SELECT Name, Capacity FROM stadium WHERE Average = (SELECT M...`

### Q19 🟢
**How many concerts are there in year 2014 or 2015?**
```sql
-- Gold: SELECT count(*) FROM concert WHERE YEAR  =  2014 OR YEAR  =  2015
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM concert WHERE YEAR IN (2014, 2015)...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM concert WHERE YEAR = '2014' OR YEAR = '...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM concert WHERE Year = '2014' OR Year = '...`

### Q20 🟢
**How many concerts occurred in 2014 or 2015?**
```sql
-- Gold: SELECT count(*) FROM concert WHERE YEAR  =  2014 OR YEAR  =  2015
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM concert WHERE YEAR IN (2014, 2015)...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM concert WHERE YEAR IN ('2014', '2015');...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM concert WHERE Year IN ('2014', '2015');...`

### Q21 🟡
**Show the stadium name and the number of concerts in each stadium.**
```sql
-- Gold: SELECT T2.name ,  count(*) FROM concert AS T1 JOIN stadium AS T2 ON T1.stadium_id  =  T2.stadium_id GROUP BY T1.stadium_id
```
- **Single_Agent** ✅: `SELECT S.Name, COUNT(C.concert_ID) AS num_concerts
FROM stad...`
- **Multi_Agent** ✅: `SELECT s.Name, COUNT(c.concert_ID) FROM concert AS c JOIN st...`
- **Multi_Agent_RAG** ✅: `SELECT s.Name, COUNT(c.concert_ID) FROM concert AS c JOIN st...`

### Q22 🟡
**For each stadium, how many concerts play there?**
```sql
-- Gold: SELECT T2.name ,  count(*) FROM concert AS T1 JOIN stadium AS T2 ON T1.stadium_id  =  T2.stadium_id GROUP BY T1.stadium_id
```
- **Single_Agent** ❌: `SELECT s.Stadium_ID, COUNT(c.concert_Name) AS num_concerts
F...`
- **Multi_Agent** ❌: `SELECT COUNT(c.concert_ID) FROM concert AS c JOIN stadium AS...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM concert AS c JOIN stadium AS s ON c.Sta...`

### Q23 🟡
**Show the stadium name and capacity with most number of concerts in year 2014 or after.**
```sql
-- Gold: SELECT T2.name ,  T2.capacity FROM concert AS T1 JOIN stadium AS T2 ON T1.stadium_id  =  T2.stadium_id WHERE T1.year  >=  2014 GROUP BY T2.stadium_id ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT s.Name, s.Capacity 
FROM stadium s 
JOIN concert c ON...`
- **Multi_Agent** ✅: `SELECT s.Name, s.Capacity FROM stadium AS s JOIN concert AS ...`
- **Multi_Agent_RAG** ❌: `SELECT Name, Capacity FROM stadium JOIN concert AS c ON stad...`

### Q24 🟡
**What is the name and capacity of the stadium with the most concerts after 2013 ?**
```sql
-- Gold: select t2.name ,  t2.capacity from concert as t1 join stadium as t2 on t1.stadium_id  =  t2.stadium_id where t1.year  >  2013 group by t2.stadium_id order by count(*) desc limit 1
```
- **Single_Agent** ❌: `SELECT s.Name, s.Capacity 
FROM stadium s 
JOIN concert c ON...`
- **Multi_Agent** ✅: `SELECT s.Name, s.Capacity FROM stadium AS s JOIN concert AS ...`
- **Multi_Agent_RAG** ✅: `SELECT s.Name, s.Capacity FROM stadium AS s JOIN concert AS ...`

### Q25 🟡
**Which year has most number of concerts?**
```sql
-- Gold: SELECT YEAR FROM concert GROUP BY YEAR ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT YEAR 
FROM concert 
GROUP BY YEAR 
ORDER BY COUNT(con...`
- **Multi_Agent** ✅: `SELECT Year FROM concert GROUP BY Year ORDER BY COUNT(*) DES...`
- **Multi_Agent_RAG** ✅: `SELECT Year FROM concert GROUP BY Year ORDER BY COUNT(*) DES...`

### Q26 🟡
**What is the year that had the most concerts?**
```sql
-- Gold: SELECT YEAR FROM concert GROUP BY YEAR ORDER BY count(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT YEAR 
FROM concert 
GROUP BY YEAR 
ORDER BY COUNT(con...`
- **Multi_Agent** ✅: `SELECT Year FROM concert GROUP BY Year ORDER BY COUNT(*) DES...`
- **Multi_Agent_RAG** ✅: `SELECT Year FROM concert GROUP BY Year ORDER BY COUNT(*) DES...`

### Q27 🟡
**Show the name and theme for all concerts and the number of singers in each concert.**
```sql
-- Gold: SELECT T2.concert_name ,  T2.theme ,  count(*) FROM singer_in_concert AS T1 JOIN concert AS T2 ON T1.concert_id  =  T2.concert_id GROUP BY T2.concert_id
```
- **Single_Agent** ✅: `SELECT 
  c.concert_Name,
  c.Theme,
  COUNT(DISTINCT si.Sin...`
- **Multi_Agent** ❌: `SELECT c.concert_Name, c.Theme, COUNT(DISTINCT si.Singer_ID)...`
- **Multi_Agent_RAG** ✅: `SELECT c.concert_Name, c.Theme, COUNT(DISTINCT si.Singer_ID)...`

### Q28 🟡
**What are the names , themes , and number of singers for every concert ?**
```sql
-- Gold: select t2.concert_name ,  t2.theme ,  count(*) from singer_in_concert as t1 join concert as t2 on t1.concert_id  =  t2.concert_id group by t2.concert_id
```
- **Single_Agent** ✅: `SELECT 
  c.concert_Name,
  c.Theme,
  COUNT(DISTINCT si.Sin...`
- **Multi_Agent** ❌: `SELECT T1.concert_Name, T2.Theme, COUNT(T3.Singer_ID) FROM c...`
- **Multi_Agent_RAG** ✅: `SELECT c.concert_Name, c.Theme, COUNT(DISTINCT si.Singer_ID)...`

### Q29 🟡
**List singer names and number of concerts for each singer.**
```sql
-- Gold: SELECT T2.name ,  count(*) FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.singer_id  =  T2.singer_id GROUP BY T2.singer_id
```
- **Single_Agent** ❌: `SELECT s.Name, COUNT(c.concert_ID) AS num_concerts
FROM sing...`
- **Multi_Agent** ✅: `SELECT s.Name, COUNT(c.concert_ID) FROM singer AS s JOIN sin...`
- **Multi_Agent_RAG** ❌: `SELECT s.Name, COUNT(sic.concert_ID) FROM singer AS sic JOIN...`

### Q30 🟡
**What are the names of the singers and number of concerts for each person?**
```sql
-- Gold: SELECT T2.name ,  count(*) FROM singer_in_concert AS T1 JOIN singer AS T2 ON T1.singer_id  =  T2.singer_id GROUP BY T2.singer_id
```
- **Single_Agent** ❌: `SELECT s.Name, COUNT(c.concert_ID) AS num_concerts
FROM sing...`
- **Multi_Agent** ✅: `SELECT s.Name, COUNT(c.concert_ID) FROM singer AS s JOIN sin...`
- **Multi_Agent_RAG** ❌: `SELECT Singer_ID, COUNT(*) FROM singer_in_concert GROUP BY S...`

### Q31 🟢
**what is the name and nation of the singer who have a song having 'Hey' in its name?**
```sql
-- Gold: SELECT name ,  country FROM singer WHERE song_name LIKE '%Hey%'
```
- **Single_Agent** ❌: `SELECT T1.Name, T1.Country 
FROM singer AS T1 
JOIN singer_i...`
- **Multi_Agent** ❌: `SELECT s.Name, s.Country FROM singer AS s JOIN singer_in_con...`
- **Multi_Agent_RAG** ❌: `SELECT s.Name, c.Country FROM singer AS s JOIN singer_in_con...`

### Q32 🟢
**What is the name and country of origin of every singer who has a song with the word 'Hey' in its title?**
```sql
-- Gold: SELECT name ,  country FROM singer WHERE song_name LIKE '%Hey%'
```
- **Single_Agent** ❌: `SELECT T1.Name, T1.Country 
FROM singer AS T1 
JOIN singer_i...`
- **Multi_Agent** ❌: `SELECT s.Name, s.Country FROM singer AS s JOIN singer_in_con...`
- **Multi_Agent_RAG** ❌: `SELECT s.Name, s.Country FROM singer AS s JOIN singer_in_con...`
