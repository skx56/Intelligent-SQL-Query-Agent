# 🤖 Multi-Agent RAG Text-to-SQL Evaluation

**Database:** world_1  
**Total Questions:** 84  
**Date:** 2025-12-21 20:25

---

## 📊 Summary - 3 Pipeline Comparison

| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |
|----------|-------------------|-----------------|-----------------|----------|
| **Single Agent** | 44.0% | 44.0% | 60.7% | 2.9s |
| **Multi Agent** | 52.4% | 52.4% | 73.3% | 10.1s |
| **Multi Agent RAG** | 59.5% | 59.5% | 75.0% | 11.4s |

### 🏆 Best: Multi Agent RAG (59.5%)

---

## 📈 Component Matching

| Pipeline | SELECT | FROM | WHERE | GROUP BY | ORDER BY |
|----------|--------|------|-------|----------|----------|
| Single Agent | 80% | 44% | 23% | 83% | 74% |
| Multi Agent | 86% | 81% | 29% | 90% | 81% |
| Multi Agent RAG | 85% | 87% | 29% | 92% | 83% |

---

## 📝 Detailed Results

### Q1 🟢
**What are the names of all the countries that became independent after 1950?**
```sql
-- Gold: SELECT Name FROM country WHERE IndepYear  >  1950
```
- **Single_Agent** ✅: `SELECT c.Name 
FROM country c 
JOIN countrylanguage cl ON c....`
- **Multi_Agent** ✅: `SELECT Name FROM country WHERE IndepYear > 1950;...`
- **Multi_Agent_RAG** ✅: `SELECT Name FROM country WHERE IndepYear > 1950;...`

### Q2 🟢
**Give the names of the nations that were founded after 1950.**
```sql
-- Gold: SELECT Name FROM country WHERE IndepYear  >  1950
```
- **Single_Agent** ✅: `SELECT c.Name 
FROM country c 
JOIN countrylanguage cl ON c....`
- **Multi_Agent** ✅: `SELECT Name FROM country WHERE IndepYear > 1950;...`
- **Multi_Agent_RAG** ✅: `SELECT Name FROM country WHERE IndepYear > 1950;...`

### Q3 🟢
**How many countries have a republic as their form of government?**
```sql
-- Gold: SELECT count(*) FROM country WHERE GovernmentForm  =  "Republic"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.Code) FROM country AS T1 INNER JOIN...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM country WHERE GovernmentForm = 'Republi...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM country WHERE GovernmentForm = 'Republi...`

### Q4 🟢
**How many countries have governments that are republics?**
```sql
-- Gold: SELECT count(*) FROM country WHERE GovernmentForm  =  "Republic"
```
- **Single_Agent** ❌: `SELECT COUNT(DISTINCT T2.Code) FROM country AS T1 INNER JOIN...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM country WHERE GovernmentForm = 'Republi...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM country WHERE GovernmentForm = 'Republi...`

### Q5 🟢
**What is the total surface area of the countries in the Caribbean region?**
```sql
-- Gold: SELECT sum(SurfaceArea) FROM country WHERE Region  =  "Caribbean"
```
- **Single_Agent** ❌: `SELECT SUM(T1.SurfaceArea) FROM country AS T1 INNER JOIN cou...`
- **Multi_Agent** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Region = 'Caribbe...`
- **Multi_Agent_RAG** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Region = 'Caribbe...`

### Q6 🟢
**How much surface area do the countires in the Carribean cover together?**
```sql
-- Gold: SELECT sum(SurfaceArea) FROM country WHERE Region  =  "Caribbean"
```
- **Single_Agent** ❌: `SELECT SUM(T1.SurfaceArea) FROM country AS T1 INNER JOIN cou...`
- **Multi_Agent** ❌: `SELECT SUM(SurfaceArea) FROM country WHERE Continent = 'Cari...`
- **Multi_Agent_RAG** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Region = 'Caribbe...`

### Q7 🟢
**Which continent is Anguilla in?**
```sql
-- Gold: SELECT Continent FROM country WHERE Name  =  "Anguilla"
```
- **Single_Agent** ❌: `SELECT T2.Continent FROM city AS T1 INNER JOIN country AS T2...`
- **Multi_Agent** ❌: `SELECT c.Continent FROM country AS c JOIN city AS ci ON c.Co...`
- **Multi_Agent_RAG** ❌: `SELECT c.Continent FROM country AS c WHERE c.Code = 'ANG';...`

### Q8 🟢
**What is the continent name which Anguilla belongs to?**
```sql
-- Gold: SELECT Continent FROM country WHERE Name  =  "Anguilla"
```
- **Single_Agent** ❌: `SELECT T2.Continent FROM country AS T1 INNER JOIN countrylan...`
- **Multi_Agent** ❌: `SELECT c.Continent FROM country AS c JOIN city AS ci ON c.Co...`
- **Multi_Agent_RAG** ❌: `SELECT c.Continent FROM country AS c WHERE c.Code = 'ANG';...`

### Q9 🟡
**Which region is the city Kabul located in?**
```sql
-- Gold: SELECT Region FROM country AS T1 JOIN city AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Name  =  "Kabul"
```
- **Single_Agent** ✅: `SELECT T2.Region FROM city AS T1 INNER JOIN country AS T2 ON...`
- **Multi_Agent** ❌: `SELECT r.Region FROM country AS c JOIN city AS ci ON c.Code ...`
- **Multi_Agent_RAG** ✅: `SELECT c.Region FROM country AS c JOIN city AS ci ON c.Code ...`

### Q10 🟡
**What region is Kabul in?**
```sql
-- Gold: SELECT Region FROM country AS T1 JOIN city AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Name  =  "Kabul"
```
- **Single_Agent** ✅: `SELECT T2.Region FROM city AS T1 INNER JOIN country AS T2 ON...`
- **Multi_Agent** ❌: `SELECT r.Region FROM country AS c JOIN city AS ci ON c.Code ...`
- **Multi_Agent_RAG** ❌: `SELECT r.Region FROM city AS c JOIN country AS co ON c.Count...`

### Q11 🟡
**Which language is the most popular in Aruba?**
```sql
-- Gold: SELECT T2.Language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Name  =  "Aruba" ORDER BY Percentage DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.Language FROM countrylanguage AS T1 INNER JOIN cou...`
- **Multi_Agent** ✅: `SELECT cl.Language FROM countrylanguage AS cl JOIN country A...`
- **Multi_Agent_RAG** ✅: `SELECT cl.Language FROM countrylanguage AS cl JOIN country A...`

### Q12 🟡
**What language is predominantly spoken in Aruba?**
```sql
-- Gold: SELECT T2.Language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Name  =  "Aruba" ORDER BY Percentage DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T2.Language FROM country AS T1 INNER JOIN countrylang...`
- **Multi_Agent** ❌: `SELECT cl.Language FROM countrylanguage AS cl JOIN country A...`
- **Multi_Agent_RAG** ❌: `SELECT cl.Language FROM country AS c JOIN countrylanguage AS...`

### Q13 🟢
**What are the population and life expectancies in Brazil?**
```sql
-- Gold: SELECT Population ,  LifeExpectancy FROM country WHERE Name  =  "Brazil"
```
- **Single_Agent** ✅: `SELECT T1.Population, T1.LifeExpectancy 
FROM country AS T1 ...`
- **Multi_Agent** ✅: `SELECT c.Population, c.LifeExpectancy FROM country AS c WHER...`
- **Multi_Agent_RAG** ✅: `SELECT Population, LifeExpectancy FROM country WHERE Name = ...`

### Q14 🟢
**Give me Brazil’s population and life expectancies.**
```sql
-- Gold: SELECT Population ,  LifeExpectancy FROM country WHERE Name  =  "Brazil"
```
- **Single_Agent** ✅: `SELECT T1.Population, T1.LifeExpectancy 
FROM country AS T1 ...`
- **Multi_Agent** ✅: `SELECT Population, LifeExpectancy FROM country WHERE Name = ...`
- **Multi_Agent_RAG** ✅: `SELECT Population, LifeExpectancy FROM country WHERE Name = ...`

### Q15 🟢
**What are the region and population of Angola?**
```sql
-- Gold: SELECT Population ,  Region FROM country WHERE Name  =  "Angola"
```
- **Single_Agent** ❌: `SELECT T2.Region, T2.Population FROM country AS T1 INNER JOI...`
- **Multi_Agent** ✅: `SELECT Region, Population FROM country WHERE Name = 'Angola'...`
- **Multi_Agent_RAG** ❌: `SELECT Region, Population FROM country WHERE Code = 'ANG';...`

### Q16 🟢
**What region does Angola belong to and what is its population?**
```sql
-- Gold: SELECT Population ,  Region FROM country WHERE Name  =  "Angola"
```
- **Single_Agent** ❌: `SELECT T2.Region, T1.Population 
FROM country AS T1 
JOIN co...`
- **Multi_Agent** ❌: `SELECT r.Region, c.Population FROM country AS c JOIN region ...`
- **Multi_Agent_RAG** ❌: `SELECT r.Region, c.Population FROM country AS c JOIN region ...`

### Q17 🟢
**What is the average expected life expectancy for countries in the region of Central Africa?**
```sql
-- Gold: SELECT avg(LifeExpectancy) FROM country WHERE Region  =  "Central Africa"
```
- **Single_Agent** ❌: `SELECT AVG(T1.LifeExpectancy) FROM country AS T1 INNER JOIN ...`
- **Multi_Agent** ✅: `SELECT AVG(LifeExpectancy) FROM country WHERE Region = 'Cent...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(LifeExpectancy) FROM country WHERE Region = 'Cent...`

### Q18 🟢
**How long is the people’s average life expectancy in Central Africa?**
```sql
-- Gold: SELECT avg(LifeExpectancy) FROM country WHERE Region  =  "Central Africa"
```
- **Single_Agent** ❌: `SELECT AVG(T1.LifeExpectancy) 
FROM country AS T1 
JOIN coun...`
- **Multi_Agent** ❌: `SELECT AVG(lifeExpectancy) FROM country WHERE Continent = 'A...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(lifeExpectancy) FROM country WHERE Continent = 'A...`

### Q19 🟢
**What is the name of country that has the shortest life expectancy in Asia?**
```sql
-- Gold: SELECT Name FROM country WHERE Continent  =  "Asia" ORDER BY LifeExpectancy LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Name 
FROM country AS T1 
JOIN countrylanguage AS ...`
- **Multi_Agent** ✅: `SELECT Name FROM country WHERE Continent = 'Asia' AND LifeEx...`
- **Multi_Agent_RAG** ✅: `SELECT Name FROM country WHERE Continent = 'Asia' AND LifeEx...`

### Q20 🟢
**Give the name of the country in Asia with the lowest life expectancy.**
```sql
-- Gold: SELECT Name FROM country WHERE Continent  =  "Asia" ORDER BY LifeExpectancy LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Name 
FROM country AS T1 
JOIN countrylanguage AS ...`
- **Multi_Agent** ✅: `SELECT Name FROM country WHERE Continent = 'Asia' ORDER BY L...`
- **Multi_Agent_RAG** ✅: `SELECT Name FROM country WHERE Continent = 'Asia' ORDER BY L...`

### Q21 🟢
**What is the total population and maximum GNP in Asia?**
```sql
-- Gold: SELECT sum(Population) ,  max(GNP) FROM country WHERE Continent  =  "Asia"
```
- **Single_Agent** ❌: `SELECT SUM(c.Population), MAX(c.GNP) 
FROM country c 
JOIN c...`
- **Multi_Agent** ❌: `SELECT SUM(Population) FROM country WHERE Continent = 'Asia'...`
- **Multi_Agent_RAG** ❌: `SELECT SUM(Population) FROM country WHERE Continent = 'Asia'...`

### Q22 🟢
**How many people live in Asia, and what is the largest GNP among them?**
```sql
-- Gold: SELECT sum(Population) ,  max(GNP) FROM country WHERE Continent  =  "Asia"
```
- **Single_Agent** ❌: `SELECT T1.Population, MAX(T2.GNP) FROM country AS T1 INNER J...`
- **Multi_Agent** ❌: `SELECT SUM(Population) FROM country WHERE Continent = 'Asia'...`
- **Multi_Agent_RAG** ❌: `SELECT SUM(Population) FROM country WHERE Continent = 'Asia'...`

### Q23 🟢
**What is the average life expectancy in African countries that are republics?**
```sql
-- Gold: SELECT avg(LifeExpectancy) FROM country WHERE Continent  =  "Africa" AND GovernmentForm  =  "Republic"
```
- **Single_Agent** ❌: `SELECT AVG(T2.LifeExpectancy) 
FROM country AS T1 
JOIN coun...`
- **Multi_Agent** ✅: `SELECT AVG(LifeExpectancy) FROM country WHERE Continent = 'A...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(LifeExpectancy) FROM country WHERE Continent = 'A...`

### Q24 🟢
**Give the average life expectancy for countries in Africa which are republics?**
```sql
-- Gold: SELECT avg(LifeExpectancy) FROM country WHERE Continent  =  "Africa" AND GovernmentForm  =  "Republic"
```
- **Single_Agent** ❌: `SELECT AVG(T1.LifeExpectancy) 
FROM country AS T1 
JOIN coun...`
- **Multi_Agent** ✅: `SELECT AVG(LifeExpectancy) FROM country WHERE Continent = 'A...`
- **Multi_Agent_RAG** ✅: `SELECT AVG(LifeExpectancy) FROM country WHERE Continent = 'A...`

### Q25 🟢
**What is the total surface area of the continents Asia and Europe?**
```sql
-- Gold: SELECT sum(SurfaceArea) FROM country WHERE Continent  =  "Asia" OR Continent  =  "Europe"
```
- **Single_Agent** ❌: `SELECT SUM(T1.SurfaceArea) FROM country AS T1 INNER JOIN cou...`
- **Multi_Agent** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Continent IN ('As...`
- **Multi_Agent_RAG** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Continent IN ('As...`

### Q26 🟢
**Give the total surface area covered by countries in Asia or Europe.**
```sql
-- Gold: SELECT sum(SurfaceArea) FROM country WHERE Continent  =  "Asia" OR Continent  =  "Europe"
```
- **Single_Agent** ❌: `SELECT SUM(T1.SurfaceArea) FROM country AS T1 INNER JOIN cou...`
- **Multi_Agent** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Continent IN ('As...`
- **Multi_Agent_RAG** ✅: `SELECT SUM(SurfaceArea) FROM country WHERE Continent IN ('As...`

### Q27 🟢
**How many people live in Gelderland district?**
```sql
-- Gold: SELECT sum(Population) FROM city WHERE District  =  "Gelderland"
```
- **Single_Agent** ❌: `SELECT T1.Population FROM city AS T1 INNER JOIN country AS T...`
- **Multi_Agent** ❌: `SELECT Population FROM city WHERE District = 'Gelderland';...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM city WHERE District = 'Gelderland';...`

### Q28 🟢
**What is the total population of Gelderland district?**
```sql
-- Gold: SELECT sum(Population) FROM city WHERE District  =  "Gelderland"
```
- **Single_Agent** ✅: `SELECT SUM(T1.Population) FROM city AS T1 INNER JOIN country...`
- **Multi_Agent** ✅: `SELECT SUM(Population) FROM city WHERE District = 'Gelderlan...`
- **Multi_Agent_RAG** ✅: `SELECT SUM(Population) FROM city WHERE District = 'Gelderlan...`

### Q29 🟢
**What is the average GNP and total population in all nations whose government is US territory?**
```sql
-- Gold: SELECT avg(GNP) ,  sum(population) FROM country WHERE GovernmentForm  =  "US Territory"
```
- **Single_Agent** ❌: `SELECT AVG(GNP) ,  SUM(Population) 
FROM country 
WHERE Gove...`
- **Multi_Agent** ❌: `SELECT AVG(GNP), SUM(Population) FROM country WHERE Code IN ...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(GNP), SUM(Population) FROM country WHERE Code2 = ...`

### Q30 🟢
**Give the mean GNP and total population of nations which are considered US territory.**
```sql
-- Gold: SELECT avg(GNP) ,  sum(population) FROM country WHERE GovernmentForm  =  "US Territory"
```
- **Single_Agent** ❌: `SELECT AVG(GNP) ,  SUM(Population) FROM country WHERE Code I...`
- **Multi_Agent** ❌: `SELECT AVG(GNP) AS mean_GNP, SUM(Population) FROM country WH...`
- **Multi_Agent_RAG** ❌: `SELECT AVG(GNP) FROM country WHERE Code = 'US';...`

### Q31 🟢
**How many unique languages are spoken in the world?**
```sql
-- Gold: SELECT count(DISTINCT LANGUAGE) FROM countrylanguage
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT Language) FROM countrylanguage...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT cl.Language) FROM countrylanguage AS c...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT Language) FROM countrylanguage;...`

### Q32 🟢
**What is the number of distinct languages used around the world?**
```sql
-- Gold: SELECT count(DISTINCT LANGUAGE) FROM countrylanguage
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT Language) FROM countrylanguage...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT Language) FROM countrylanguage;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT Language) FROM countrylanguage;...`

### Q33 🟢
**How many type of governments are in Africa?**
```sql
-- Gold: SELECT count(DISTINCT GovernmentForm) FROM country WHERE Continent  =  "Africa"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Con...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Con...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Con...`

### Q34 🟢
**How many different forms of governments are there in Africa?**
```sql
-- Gold: SELECT count(DISTINCT GovernmentForm) FROM country WHERE Continent  =  "Africa"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Con...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Con...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT GovernmentForm) FROM country WHERE Con...`

### Q35 🟡
**What is the total number of languages used in Aruba?**
```sql
-- Gold: SELECT COUNT(T2.Language) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Name  =  "Aruba"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T1.Language) FROM countrylanguage AS T...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM countrylanguage AS cl JOIN country AS c...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = 'AB...`

### Q36 🟡
**How many languages are spoken in Aruba?**
```sql
-- Gold: SELECT COUNT(T2.Language) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Name  =  "Aruba"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T2.Language) FROM country AS T1 INNER ...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT cl.Language) FROM countrylanguage AS c...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = 'AB...`

### Q37 🟡
**How many official languages does Afghanistan have?**
```sql
-- Gold: SELECT COUNT(*) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Name  =  "Afghanistan" AND IsOfficial  =  "T"
```
- **Single_Agent** ✅: `SELECT COUNT(T1.Language) FROM countrylanguage AS T1 INNER J...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT cl.Language) FROM countrylanguage AS c...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = 'AF...`

### Q38 🟡
**How many official languages are spoken in Afghanistan?**
```sql
-- Gold: SELECT COUNT(*) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Name  =  "Afghanistan" AND IsOfficial  =  "T"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T2.Language) FROM country AS T1 INNER ...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT cl.Language) FROM countrylanguage AS c...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = 'AF...`

### Q39 🟡
**What is name of the country that speaks the largest number of languages?**
```sql
-- Gold: SELECT T1.Name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode GROUP BY T1.Name ORDER BY COUNT(*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Name 
FROM country AS T1 
JOIN countrylanguage AS ...`
- **Multi_Agent** ❌: `SELECT cl.Language FROM countrylanguage AS cl JOIN country A...`
- **Multi_Agent_RAG** ✅: `SELECT c.Name FROM country AS c JOIN countrylanguage AS cl O...`

### Q40 🟡
**Give the name of the nation that uses the greatest amount of languages.**
```sql
-- Gold: SELECT T1.Name FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode GROUP BY T1.Name ORDER BY COUNT(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.Name 
FROM country AS T1 
JOIN countrylanguage AS ...`
- **Multi_Agent** ❌: `SELECT cl.Language FROM countrylanguage AS cl GROUP BY cl.Co...`
- **Multi_Agent_RAG** ❌: `SELECT cl.Language FROM countrylanguage AS cl JOIN country A...`

### Q41 🟡
**Which continent has the most diverse languages?**
```sql
-- Gold: SELECT T1.Continent FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode GROUP BY T1.Continent ORDER BY COUNT(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.Continent 
FROM country AS T1 
JOIN countrylanguag...`
- **Multi_Agent** ❌: `SELECT c.Continent, COUNT(DISTINCT cl.Language) FROM country...`
- **Multi_Agent_RAG** ❌: `SELECT c.Continent, COUNT(DISTINCT cl.Language) FROM country...`

### Q42 🟡
**Which continent speaks the most languages?**
```sql
-- Gold: SELECT T1.Continent FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode GROUP BY T1.Continent ORDER BY COUNT(*) DESC LIMIT 1
```
- **Single_Agent** ✅: `SELECT T1.Continent FROM country AS T1 INNER JOIN countrylan...`
- **Multi_Agent** ❌: `SELECT cl.Percentage FROM countrylanguage AS cl JOIN country...`
- **Multi_Agent_RAG** ❌: `SELECT c.Continent, COUNT(cl.Language) FROM countrylanguage ...`

### Q43 🟡
**What is the number of distinct continents where Chinese is spoken?**
```sql
-- Gold: SELECT COUNT( DISTINCT Continent) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Language  =  "Chinese"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T2.Continent) FROM countrylanguage AS ...`
- **Multi_Agent** ✅: `SELECT COUNT(DISTINCT c.Continent) FROM countrylanguage AS c...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(DISTINCT c.Continent) FROM countrylanguage AS c...`

### Q44 🟡
**How many continents speak Chinese?**
```sql
-- Gold: SELECT COUNT( DISTINCT Continent) FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Language  =  "Chinese"
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T2.Continent) FROM countrylanguage AS ...`
- **Multi_Agent** ❌: `SELECT COUNT(DISTINCT cl.Language) FROM countrylanguage AS c...`
- **Multi_Agent_RAG** ❌: `SELECT COUNT(DISTINCT cl.CountryCode) FROM countrylanguage A...`

### Q45 🟡
**What are the regions that use English or Dutch?**
```sql
-- Gold: SELECT DISTINCT T1.Region FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Language  =  "English" OR T2.Language  =  "Dutch"
```
- **Single_Agent** ✅: `SELECT T2.Region 
FROM countrylanguage AS T1 
JOIN country A...`
- **Multi_Agent** ❌: `SELECT r.Region FROM countrylanguage AS cl JOIN country AS c...`
- **Multi_Agent_RAG** ✅: `SELECT c.Region FROM country AS c JOIN countrylanguage AS cl...`

### Q46 🟡
**Which regions speak Dutch or English?**
```sql
-- Gold: SELECT DISTINCT T1.Region FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T2.Language  =  "English" OR T2.Language  =  "Dutch"
```
- **Single_Agent** ✅: `SELECT T1.Region 
FROM country AS T1 
JOIN countrylanguage A...`
- **Multi_Agent** ❌: `SELECT cl.Percentage FROM countrylanguage AS cl JOIN country...`
- **Multi_Agent_RAG** ❌: `SELECT cl.Percentage FROM countrylanguage AS cl JOIN country...`

### Q47 🟡
**Which language is the most popular on the Asian continent?**
```sql
-- Gold: SELECT T2.Language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Continent  =  "Asia" GROUP BY T2.Language ORDER BY COUNT (*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Language FROM country AS T1 INNER JOIN countrylang...`
- **Multi_Agent** ❌: `SELECT cl.Language FROM country AS c JOIN countrylanguage AS...`
- **Multi_Agent_RAG** ❌: `SELECT cl.Language FROM country AS c JOIN countrylanguage AS...`

### Q48 🟡
**What is the language that is used by the largest number of Asian nations?**
```sql
-- Gold: SELECT T2.Language FROM country AS T1 JOIN countrylanguage AS T2 ON T1.Code  =  T2.CountryCode WHERE T1.Continent  =  "Asia" GROUP BY T2.Language ORDER BY COUNT (*) DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Language FROM country AS T1 INNER JOIN countrylang...`
- **Multi_Agent** ✅: `SELECT cl.Language FROM countrylanguage AS cl JOIN country A...`
- **Multi_Agent_RAG** ✅: `SELECT cl.Language FROM country AS c JOIN countrylanguage AS...`

### Q49 🟡
**Find the city with the largest population that uses English.**
```sql
-- Gold: SELECT T1.Name ,  T1.Population FROM city AS T1 JOIN countrylanguage AS T2 ON T1.CountryCode  =  T2.CountryCode WHERE T2.Language  =  "English" ORDER BY T1.Population DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT c.Name FROM country AS c 
JOIN countrylanguage AS cl ...`
- **Multi_Agent** ❌: `SELECT c.Name FROM countrylanguage AS cl JOIN country AS c O...`
- **Multi_Agent_RAG** ❌: `SELECT c.Name FROM city AS c JOIN countrylanguage AS cl ON c...`

### Q50 🟡
**What is the most populace city that speaks English?**
```sql
-- Gold: SELECT T1.Name ,  T1.Population FROM city AS T1 JOIN countrylanguage AS T2 ON T1.CountryCode  =  T2.CountryCode WHERE T2.Language  =  "English" ORDER BY T1.Population DESC LIMIT 1
```
- **Single_Agent** ❌: `SELECT T1.Name FROM countrylanguage AS T1 INNER JOIN country...`
- **Multi_Agent** ❌: `SELECT c.Name FROM countrylanguage AS cl JOIN country AS c O...`
- **Multi_Agent_RAG** ❌: `SELECT c.Name FROM city AS c JOIN countrylanguage AS cl ON c...`

*... and 34 more questions*