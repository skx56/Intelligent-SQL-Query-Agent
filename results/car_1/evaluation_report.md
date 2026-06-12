# 🤖 Multi-Agent RAG Text-to-SQL Evaluation

**Database:** car_1  
**Total Questions:** 58  
**Date:** 2025-12-21 21:22

---

## 📊 Summary - 3 Pipeline Comparison

| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |
|----------|-------------------|-----------------|-----------------|----------|
| **Single Agent** | 39.7% | 39.7% | 76.2% | 2.8s |
| **Multi Agent** | 27.6% | 27.6% | 74.8% | 9.5s |
| **Multi Agent RAG** | 44.8% | 44.8% | 77.6% | 21.2s |

### 🏆 Best: Multi Agent RAG (44.8%)

---

## 📈 Component Matching

| Pipeline | SELECT | FROM | WHERE | GROUP BY | ORDER BY |
|----------|--------|------|-------|----------|----------|
| Single Agent | 83% | 62% | 79% | 78% | 79% |
| Multi Agent | 84% | 45% | 79% | 81% | 84% |
| Multi Agent RAG | 83% | 60% | 79% | 83% | 83% |

---

## 📝 Detailed Results

### Q1 🟢
**How many continents are there?**
```sql
-- Gold: SELECT count(*) FROM CONTINENTS;
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.Continent) FROM continents AS T1...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM continents;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM continents;...`

### Q2 🟢
**What is the number of continents?**
```sql
-- Gold: SELECT count(*) FROM CONTINENTS;
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.Continent) FROM continents AS T1...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM continents;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM continents;...`

### Q3 🟡
**How many countries does each continent have? List the continent id, continent name and the number of countries.**
```sql
-- Gold: SELECT T1.ContId ,  T1.Continent ,  count(*) FROM CONTINENTS AS T1 JOIN COUNTRIES AS T2 ON T1.ContId  =  T2.Continent GROUP BY T1.ContId;
```
- **Single_Agent** ❌: `SELECT 
  c.ContId,
  c.Continent,
  COUNT(DISTINCT c.Contin...`
- **Multi_Agent** ✅: `SELECT c.ContId, c.Continent, COUNT(*) FROM continents AS c ...`
- **Multi_Agent_RAG** ✅: `SELECT c.ContId, c.Continent, COUNT(*) FROM continents AS c ...`

### Q4 🟡
**For each continent, list its id, name, and how many countries it has?**
```sql
-- Gold: SELECT T1.ContId ,  T1.Continent ,  count(*) FROM CONTINENTS AS T1 JOIN COUNTRIES AS T2 ON T1.ContId  =  T2.Continent GROUP BY T1.ContId;
```
- **Single_Agent** ❌: `SELECT 
  c.ContId,
  c.Continent,
  COUNT(DISTINCT cn.Count...`
- **Multi_Agent** ❌: `SELECT c.ContId, c.Continent, COUNT(c.CountryId) FROM contin...`
- **Multi_Agent_RAG** ❌: `SELECT c.ContId, c.Continent, COUNT(c.CountryId) FROM countr...`

### Q5 🟢
**How many countries are listed?**
```sql
-- Gold: SELECT count(*) FROM COUNTRIES;
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.CountryName) FROM countries AS T1 I...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM country;...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM country;...`

### Q6 🟢
**How many countries exist?**
```sql
-- Gold: SELECT count(*) FROM COUNTRIES;
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.CountryName) FROM countries AS T1 I...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM country;...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM country;...`

### Q7 🟡
**How many models does each car maker produce? List maker full name, id and the number.**
```sql
-- Gold: SELECT T1.FullName ,  T1.Id ,  count(*) FROM CAR_MAKERS AS T1 JOIN MODEL_LIST AS T2 ON T1.Id  =  T2.Maker GROUP BY T1.Id;
```
- **Single_Agent** ❌: `SELECT 
  c.FullName,
  m.ModelId,
  COUNT(m.ModelId) AS Num...`
- **Multi_Agent** ❌: `SELECT c.Maker, c.FullName, COUNT(*) FROM car_makers AS c JO...`
- **Multi_Agent_RAG** ❌: `SELECT c.Maker, c.Id, COUNT(m.ModelId) AS ModelCount FROM ca...`

### Q8 🟡
**What is the full name of each car maker, along with its id and how many models it produces?**
```sql
-- Gold: SELECT T1.FullName ,  T1.Id ,  count(*) FROM CAR_MAKERS AS T1 JOIN MODEL_LIST AS T2 ON T1.Id  =  T2.Maker GROUP BY T1.Id;
```
- **Single_Agent** ✅: `SELECT 
  c.Id,
  c.FullName,
  COUNT(ml.ModelId) AS NumberO...`
- **Multi_Agent** ❌: `SELECT c.Id, c.Maker, COUNT(m.ModelId) AS ModelCount FROM ca...`
- **Multi_Agent_RAG** ❌: `SELECT c.Id, c.FullName, COUNT(m.MakeId) FROM car_makers AS ...`

### Q9 🟡
**Which model of the car has the minimum horsepower?**
```sql
-- Gold: SELECT T1.Model FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id ORDER BY T2.horsepower ASC LIMIT 1;
```
- **Single_Agent** ❌: `SELECT Model FROM cars_data AS cd 
JOIN car_names AS cn ON c...`
- **Multi_Agent** ❌: `SELECT MIN(Horsepower) FROM cars_data;...`
- **Multi_Agent_RAG** ❌: `SELECT MIN(Horsepower) FROM cars_data AS c;...`

### Q10 🟡
**What is the model of the car with the smallest amount of horsepower?**
```sql
-- Gold: SELECT T1.Model FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id ORDER BY T2.horsepower ASC LIMIT 1;
```
- **Single_Agent** ❌: `SELECT Model FROM cars_data AS cd 
JOIN car_names AS cn ON c...`
- **Multi_Agent** ❌: `SELECT Model FROM car_names JOIN cars_data AS cd ON MakeId =...`
- **Multi_Agent_RAG** ✅: `SELECT Model FROM car_names AS c JOIN cars_data AS cd ON c.M...`

### Q11 🟡
**Which of the countries has the most car makers? List the country name.**
```sql
-- Gold: SELECT T2.CountryName FROM CAR_MAKERS AS T1 JOIN COUNTRIES AS T2 ON T1.Country  =  T2.CountryId GROUP BY T1.Country ORDER BY Count(*) DESC LIMIT 1;
```
- **Single_Agent** ✅: `SELECT T1.CountryName 
FROM countries AS T1 
JOIN car_makers...`
- **Multi_Agent** ❌: `SELECT c.Name FROM country AS c JOIN car_makers AS cm ON c.C...`
- **Multi_Agent_RAG** ❌: `SELECT c.Name FROM country AS c JOIN car_makers AS cm ON c.C...`

### Q12 🟡
**What is the name of the country with the most car makers?**
```sql
-- Gold: SELECT T2.CountryName FROM CAR_MAKERS AS T1 JOIN COUNTRIES AS T2 ON T1.Country  =  T2.CountryId GROUP BY T1.Country ORDER BY Count(*) DESC LIMIT 1;
```
- **Single_Agent** ✅: `SELECT T2.CountryName 
FROM car_makers AS T1 
JOIN countries...`
- **Multi_Agent** ❌: `SELECT c.Name FROM countries AS c JOIN car_makers AS cm ON c...`
- **Multi_Agent_RAG** ❌: `SELECT c.Name FROM country AS c JOIN car_makers AS cm ON c.C...`

### Q13 🟡
**How many car models are produced by each maker ? Only list the count and the maker full name .**
```sql
-- Gold: select count(*) ,  t2.fullname from model_list as t1 join car_makers as t2 on t1.maker  =  t2.id group by t2.id;
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT c.Maker), cm.FullName 
FROM car_makers...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT m.Maker), m.FullName FROM model_list A...`
- **Multi_Agent_RAG** ❌: `SELECT m.Maker, COUNT(c.Model) FROM car_names AS c JOIN car_...`

### Q14 🟡
**What is the number of car models that are produced by each maker and what is the id and full name of each maker?**
```sql
-- Gold: SELECT Count(*) ,  T2.FullName ,  T2.id FROM MODEL_LIST AS T1 JOIN CAR_MAKERS AS T2 ON T1.Maker  =  T2.Id GROUP BY T2.id;
```
- **Single_Agent** ✅: `SELECT 
  c.Id AS MakerId,
  c.FullName,
  COUNT(DISTINCT m....`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT ModelId) AS Count, m.Id, m.FullName FR...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(cm.MakeId) AS ModelCount, m.Id, m.FullName FROM...`

### Q15 🟡
**What is the accelerate of the car make amc hornet sportabout (sw)?**
```sql
-- Gold: SELECT T1.Accelerate FROM CARS_DATA AS T1 JOIN CAR_NAMES AS T2 ON T1.Id  =  T2.MakeId WHERE T2.Make  =  'amc hornet sportabout (sw)';
```
- **Single_Agent** ❌: `SELECT T1.Accelerate 
FROM cars_data AS T1 
JOIN car_names A...`
- **Multi_Agent** ❌: `SELECT c.Accelerate FROM cars_data AS c JOIN model_list AS m...`
- **Multi_Agent_RAG** ❌: `SELECT c.Accelerate FROM cars_data AS c JOIN car_names AS cn...`

### Q16 🟡
**How much does the car accelerate that makes amc hornet sportabout (sw)?**
```sql
-- Gold: SELECT T1.Accelerate FROM CARS_DATA AS T1 JOIN CAR_NAMES AS T2 ON T1.Id  =  T2.MakeId WHERE T2.Make  =  'amc hornet sportabout (sw)';
```
- **Single_Agent** ❌: `SELECT T1.Accelerate 
FROM cars_data AS T1 
JOIN car_names A...`
- **Multi_Agent** ❌: `SELECT Edispl FROM cars_data WHERE Model = 'amc hornet sport...`
- **Multi_Agent_RAG** ❌: `SELECT Accelerate FROM cars_data WHERE Make = 'AMC' AND Mode...`

### Q17 🟡
**How many car makers are there in france?**
```sql
-- Gold: SELECT count(*) FROM CAR_MAKERS AS T1 JOIN COUNTRIES AS T2 ON T1.Country  =  T2.CountryId WHERE T2.CountryName  =  'france';
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.Maker) FROM car_makers AS T1 INNER ...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT c.Maker) FROM car_makers AS c JOIN cou...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM car_makers WHERE Country = 'France';...`

### Q18 🟡
**What is the number of makers of care in France?**
```sql
-- Gold: SELECT count(*) FROM CAR_MAKERS AS T1 JOIN COUNTRIES AS T2 ON T1.Country  =  T2.CountryId WHERE T2.CountryName  =  'france';
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.Maker) FROM car_makers AS T1 INNER ...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT c.Maker) FROM car_makers AS c JOIN cou...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM car_makers WHERE Country = 'France';...`

### Q19 🟢
**What is the average miles per gallon(mpg) of the cars with 4 cylinders?**
```sql
-- Gold: SELECT avg(mpg) FROM CARS_DATA WHERE Cylinders  =  4;
```
- **Single_Agent** ❌: `SELECT AVG(T1.MPG) FROM cars_data AS T1 INNER JOIN car_maker...`
- **Multi_Agent** ✅: `SELECT AVG(c.MPG) FROM cars_data AS c WHERE c.Cylinders = 4;...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(MPG) FROM cars_data WHERE Cylinders = 4;...`

### Q20 🟢
**What is the average miles per gallon of all the cards with 4 cylinders?**
```sql
-- Gold: SELECT avg(mpg) FROM CARS_DATA WHERE Cylinders  =  4;
```
- **Single_Agent** ❌: `SELECT AVG(T1.MPG) 
FROM cars_data AS T1 
JOIN car_makers AS...`
- **Multi_Agent** ✅: `SELECT AVG(c.MPG) FROM cars_data AS c WHERE c.Cylinders = 4;...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(MPG) FROM cars_data WHERE Cylinders = 4;...`

### Q21 🟢
**What is the smallest weight of the car produced with 8 cylinders on 1974 ?**
```sql
-- Gold: select min(weight) from cars_data where cylinders  =  8 and year  =  1974
```
- **Single_Agent** ✅: `SELECT MIN(Weight) 
FROM cars_data 
WHERE Cylinders = 8 AND ...`
- **Multi_Agent** ✅: `SELECT MIN(Weight) FROM cars_data WHERE Cylinders = 8 AND Ye...`
- **Multi_Agent_RAG** ✅: `SELECT MIN(Weight) FROM cars_data WHERE Cylinders = 8 AND Ye...`

### Q22 🟢
**What is the minimum weight of the car with 8 cylinders produced in 1974 ?**
```sql
-- Gold: select min(weight) from cars_data where cylinders  =  8 and year  =  1974
```
- **Single_Agent** ✅: `SELECT MIN(Weight) 
FROM cars_data 
WHERE Cylinders = 8 AND ...`
- **Multi_Agent** ✅: `SELECT MIN(Weight) FROM cars_data WHERE Cylinders = 8 AND Ye...`
- **Multi_Agent_RAG** ✅: `SELECT MIN(Weight) FROM cars_data WHERE Cylinders = 8 AND Ye...`

### Q23 🟢
**What are all the makers and models?**
```sql
-- Gold: SELECT Maker ,  Model FROM MODEL_LIST;
```
- **Single_Agent** ❌: `SELECT T1.Maker, T2.Model 
FROM car_makers AS T1 
INNER JOIN...`
- **Multi_Agent** ❌: `SELECT Maker, Model FROM car_makers JOIN model_list ON car_m...`
- **Multi_Agent_RAG** ❌: `SELECT c.Maker, cn.Model FROM car_makers AS c JOIN car_names...`

### Q24 🟢
**What are the makers and models?**
```sql
-- Gold: SELECT Maker ,  Model FROM MODEL_LIST;
```
- **Single_Agent** ❌: `SELECT T1.Maker, T2.Model 
FROM car_makers AS T1 
INNER JOIN...`
- **Multi_Agent** ❌: `SELECT Maker, Model FROM car_makers JOIN model_list ON car_m...`
- **Multi_Agent_RAG** ❌: `SELECT c.Maker, cn.Model FROM car_makers AS c JOIN car_names...`

### Q25 🟢
**What is the number of the cars with horsepower more than 150?**
```sql
-- Gold: SELECT count(*) FROM CARS_DATA WHERE horsepower  >  150;
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM cars_data WHERE Horsepower > '150'...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM cars_data WHERE Horsepower > '150';...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM cars_data WHERE Horsepower > '150';...`

### Q26 🟢
**What is the number of cars with a horsepower greater than 150?**
```sql
-- Gold: SELECT count(*) FROM CARS_DATA WHERE horsepower  >  150;
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM cars_data WHERE Horsepower > '150'...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM car_names AS cn JOIN cars_data AS c ON ...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM cars_data WHERE Horsepower > '150';...`

### Q27 🟡
**What is the average weight of cars each year?**
```sql
-- Gold: SELECT avg(Weight) ,  YEAR FROM CARS_DATA GROUP BY YEAR;
```
- **Single_Agent** ❌: `SELECT AVG(CASE WHEN Year = 2010 THEN Weight ELSE NULL END) ...`
- **Multi_Agent** ❌: `SELECT AVG(Weight) FROM cars_data;...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(Weight) FROM cars_data;...`

### Q28 🟡
**What is the average weight and year for each year?**
```sql
-- Gold: SELECT avg(Weight) ,  YEAR FROM CARS_DATA GROUP BY YEAR;
```
- **Single_Agent** ❌: `SELECT AVG(Weight) AS avg_weight, AVG(Year) AS avg_year 
FRO...`
- **Multi_Agent** ❌: `SELECT AVG(Weight) AS avg_weight, AVG(Year) AS avg_year FROM...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(Weight), AVG(Year) FROM cars_data GROUP BY Year;...`

### Q29 🟡
**What is the maximum horsepower and the make of the car models with 3 cylinders?**
```sql
-- Gold: SELECT T2.horsepower ,  T1.Make FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id WHERE T2.cylinders  =  3 ORDER BY T2.horsepower DESC LIMIT 1;
```
- **Single_Agent** ❌: `SELECT T1.MPG, T1.Horsepower 
FROM cars_data AS T1 
JOIN car...`
- **Multi_Agent** ❌: `SELECT MAX(Horsepower) FROM cars_data WHERE Cylinders = 3;...`
- **Multi_Agent_RAG** ❌: `SELECT MAX(Horsepower) FROM cars_data JOIN car_names ON cars...`

### Q30 🟡
**What is the largest amount of horsepower for the models with 3 cylinders and what make is it?**
```sql
-- Gold: SELECT T2.horsepower ,  T1.Make FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id WHERE T2.cylinders  =  3 ORDER BY T2.horsepower DESC LIMIT 1;
```
- **Single_Agent** ❌: `SELECT T1.Model, T2.Make 
FROM cars_data AS T1 
JOIN car_nam...`
- **Multi_Agent** ❌: `SELECT MAX(c.Horsepower) FROM cars_data AS c JOIN model_list...`
- **Multi_Agent_RAG** ❌: `SELECT MAX(Horsepower) FROM cars_data WHERE Cylinders = 3 AN...`

### Q31 🟡
**Which model saves the most gasoline? That is to say, have the maximum miles per gallon.**
```sql
-- Gold: SELECT T1.Model FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id ORDER BY T2.mpg DESC LIMIT 1;
```
- **Single_Agent** ✅: `SELECT Model FROM cars_data AS t1 INNER JOIN car_names AS t2...`
- **Multi_Agent** ❌: `SELECT Model FROM car_names JOIN cars_data ON MakeId = Id WH...`
- **Multi_Agent_RAG** ❌: `SELECT MAX(MPG) FROM cars_data;...`

### Q32 🟡
**What is the car model with the highest mpg ?**
```sql
-- Gold: select t1.model from car_names as t1 join cars_data as t2 on t1.makeid  =  t2.id order by t2.mpg desc limit 1;
```
- **Single_Agent** ❌: `SELECT Model FROM cars_data AS cd 
JOIN car_names AS cn ON c...`
- **Multi_Agent** ❌: `SELECT Model FROM model_list ORDER BY MPG DESC LIMIT 1;...`
- **Multi_Agent_RAG** ❌: `SELECT Model FROM models JOIN car_names ON models.ModelId = ...`

### Q33 🟢
**What is the average horsepower of the cars before 1980?**
```sql
-- Gold: SELECT avg(horsepower) FROM CARS_DATA WHERE YEAR  <  1980;
```
- **Single_Agent** ✅: `SELECT AVG(CASE WHEN Year < 1980 THEN Horsepower ELSE NULL E...`
- **Multi_Agent** ❌: `SELECT AVG(CarsData.Horsepower) FROM cars_data WHERE CarsDat...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(Horsepower) FROM cars_data WHERE Year < 1980;...`

### Q34 🟢
**What is the average horsepower for all cars produced before 1980 ?**
```sql
-- Gold: select avg(horsepower) from cars_data where year  <  1980;
```
- **Single_Agent** ❌: `SELECT AVG(T1.Horsepower) 
FROM cars_data AS T1 
JOIN car_ma...`
- **Multi_Agent** ❌: `SELECT AVG(CarsData.Horsepower) FROM cars_data AS cd JOIN ca...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(Horsepower) FROM cars_data WHERE Year < 1980;...`

### Q35 🟡
**What is the average edispl of the cars of model volvo?**
```sql
-- Gold: SELECT avg(T2.edispl) FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id WHERE T1.Model  =  'volvo';
```
- **Single_Agent** ❌: `SELECT AVG(Edispl) FROM cars_data AS cd INNER JOIN car_names...`
- **Multi_Agent** ❌: `SELECT AVG(Edispl) FROM cars_data AS c JOIN model_list AS m ...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(Edispl) FROM cars_data AS cd JOIN car_names AS cn...`

### Q36 🟡
**What is the average edispl for all volvos?**
```sql
-- Gold: SELECT avg(T2.edispl) FROM CAR_NAMES AS T1 JOIN CARS_DATA AS T2 ON T1.MakeId  =  T2.Id WHERE T1.Model  =  'volvo';
```
- **Single_Agent** ❌: `SELECT AVG(Edispl) FROM cars_data AS cd 
JOIN car_names AS c...`
- **Multi_Agent** ❌: `SELECT AVG(Edispl) FROM cars_data WHERE Make = 'Volvo';...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(Edispl) FROM volvo_table;...`

### Q37 🟡
**What is the maximum accelerate for different number of cylinders?**
```sql
-- Gold: SELECT max(Accelerate) ,  Cylinders FROM CARS_DATA GROUP BY Cylinders;
```
- **Single_Agent** ✅: `SELECT C.Cylinders, MAX(C.Accelerate) as MaxAccelerate
FROM ...`
- **Multi_Agent** ❌: `SELECT MAX(Accelerate) FROM cars_data JOIN car_makers ON car...`
- **Multi_Agent_RAG** ❌: `SELECT MAX(Accelerate) FROM cars_data AS c JOIN cylinders AS...`

### Q38 🟡
**What is the maximum accelerate for all the different cylinders?**
```sql
-- Gold: SELECT max(Accelerate) ,  Cylinders FROM CARS_DATA GROUP BY Cylinders;
```
- **Single_Agent** ❌: `SELECT MAX(T1.Accelerate) FROM cars_data AS T1 INNER JOIN ca...`
- **Multi_Agent** ❌: `SELECT MAX(accelerate) FROM cars_data JOIN car_makers ON car...`
- **Multi_Agent_RAG** ❌: `SELECT MAX(Accelerate) FROM cars_data AS c JOIN car_names AS...`

### Q39 🟡
**Which model has the most version(make) of cars?**
```sql
-- Gold: SELECT Model FROM CAR_NAMES GROUP BY Model ORDER BY count(*) DESC LIMIT 1;
```
- **Single_Agent** ✅: `SELECT Model FROM car_names GROUP BY Model ORDER BY COUNT(Ma...`
- **Multi_Agent** ❌: `SELECT ModelId FROM car_makers JOIN model_list ON car_makers...`
- **Multi_Agent_RAG** ❌: `SELECT Model FROM car_names JOIN model_list ON car_names.Mak...`

### Q40 🟡
**What model has the most different versions?**
```sql
-- Gold: SELECT Model FROM CAR_NAMES GROUP BY Model ORDER BY count(*) DESC LIMIT 1;
```
- **Single_Agent** ✅: `SELECT Model FROM ( SELECT Model, COUNT(DISTINCT MakeId) AS ...`
- **Multi_Agent** ❌: `SELECT Model FROM model_list GROUP BY Model ORDER BY COUNT(*...`
- **Multi_Agent_RAG** ❌: `SELECT ModelId FROM model_list GROUP BY ModelId ORDER BY COU...`

### Q41 🟢
**How many cars have more than 4 cylinders?**
```sql
-- Gold: SELECT count(*) FROM CARS_DATA WHERE Cylinders  >  4;
```
- **Single_Agent** ❌: `SELECT COUNT(*) FROM cars_data AS cd 
JOIN car_makers AS cm ...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM car_makers WHERE Cylinders > 4;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM cars_data WHERE Cylinders > 4;...`

### Q42 🟢
**What is the number of cars with more than 4 cylinders?**
```sql
-- Gold: SELECT count(*) FROM CARS_DATA WHERE Cylinders  >  4;
```
- **Single_Agent** ✅: `SELECT COUNT(*) FROM cars_data WHERE Cylinders > 4...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM car_makers WHERE Cylinders > 4;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM cars_data WHERE Cylinders > 4;...`

### Q43 🟢
**how many cars were produced in 1980?**
```sql
-- Gold: SELECT count(*) FROM CARS_DATA WHERE YEAR  =  1980;
```
- **Single_Agent** ❌: `SELECT COUNT(T1.Id) FROM cars_data AS T1 INNER JOIN car_make...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM car_makers JOIN cars_data ON car_makers...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM cars_data WHERE Year = 1980;...`

### Q44 🟢
**In 1980, how many cars were made?**
```sql
-- Gold: SELECT count(*) FROM CARS_DATA WHERE YEAR  =  1980;
```
- **Single_Agent** ❌: `SELECT COUNT(T1.Id) FROM cars_data AS T1 INNER JOIN car_make...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM car_makers WHERE Year = 1980;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM cars_data WHERE Year = 1980;...`

### Q45 🟡
**How many car models were produced by the maker with full name American Motor Company?**
```sql
-- Gold: SELECT count(*) FROM CAR_MAKERS AS T1 JOIN MODEL_LIST AS T2 ON T1.Id  =  T2.Maker WHERE T1.FullName  =  'American Motor Company';
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.ModelId) 
FROM car_names AS T1 
JOI...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM model_list AS ml JOIN car_makers AS cm ...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM model_list AS ml JOIN car_names AS cn O...`

### Q46 🟡
**What is the number of car models created by the car maker American Motor Company?**
```sql
-- Gold: SELECT count(*) FROM CAR_MAKERS AS T1 JOIN MODEL_LIST AS T2 ON T1.Id  =  T2.Maker WHERE T1.FullName  =  'American Motor Company';
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T1.ModelId) FROM model_list AS T1 INNE...`
- **Multi_Agent** ❌: `SELECT COUNT(*) FROM car_model AS cm JOIN car_maker AS cm_m ...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM car_names AS c JOIN car_makers AS m ON ...`

### Q47 🟢
**In which years cars were produced weighing no less than 3000 and no more than 4000 ?**
```sql
-- Gold: select distinct year from cars_data where weight between 3000 and 4000;
```
- **Single_Agent** ✅: `SELECT Year FROM cars_data WHERE Weight BETWEEN 3000 AND 400...`
- **Multi_Agent** ✅: `SELECT Year FROM cars_data WHERE Weight BETWEEN 3000 AND 400...`
- **Multi_Agent_RAG** ✅: `SELECT Year FROM cars_data WHERE Weight BETWEEN 3000 AND 400...`

### Q48 🟢
**What are the different years in which there were cars produced that weighed less than 4000 and also cars that weighted more than 3000 ?**
```sql
-- Gold: select distinct year from cars_data where weight between 3000 and 4000;
```
- **Single_Agent** ✅: `SELECT DISTINCT Year 
FROM cars_data 
WHERE Weight < 4000 OR...`
- **Multi_Agent** ✅: `SELECT DISTINCT Year FROM cars_data WHERE Weight < 4000 INTE...`
- **Multi_Agent_RAG** ✅: `SELECT DISTINCT Year FROM cars_data WHERE Weight < 4000 INTE...`

### Q49 🟢
**What is the horsepower of the car with the largest accelerate?**
```sql
-- Gold: SELECT T1.horsepower FROM CARS_DATA AS T1 ORDER BY T1.accelerate DESC LIMIT 1;
```
- **Single_Agent** ❌: `SELECT T1.Horsepower 
FROM cars_data AS T1 
JOIN model_list ...`
- **Multi_Agent** ✅: `SELECT MAX(CASE WHEN Id = (SELECT Id FROM cars_data ORDER BY...`
- **Multi_Agent_RAG** ❌: `SELECT Horsepower FROM cars_data WHERE Id = (SELECT MAX(Id) ...`

### Q50 🟢
**What is the horsepower of the car with the greatest accelerate?**
```sql
-- Gold: SELECT T1.horsepower FROM CARS_DATA AS T1 ORDER BY T1.accelerate DESC LIMIT 1;
```
- **Single_Agent** ❌: `SELECT T1.Horsepower 
FROM cars_data AS T1 
JOIN model_list ...`
- **Multi_Agent** ✅: `SELECT MAX(CASE WHEN Id = (SELECT Id FROM cars_data ORDER BY...`
- **Multi_Agent_RAG** ✅: `SELECT Horsepower FROM cars_data WHERE Accelerate = (SELECT ...`

*... and 8 more questions*