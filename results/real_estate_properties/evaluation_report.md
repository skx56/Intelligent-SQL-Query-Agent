# 🤖 Multi-Agent RAG Text-to-SQL Evaluation

**Database:** real_estate_properties  
**Total Questions:** 3  
**Date:** 2025-12-01 14:36

---

## 📊 Summary - 3 Pipeline Karşılaştırması

| Pipeline | Execution Accuracy | Exact Set Match | Component Score | Avg Time |
|----------|-------------------|-----------------|-----------------|----------|
| **Single Agent** | 66.7% | 66.7% | 66.7% | 3.3s |
| **Multi Agent** | 66.7% | 66.7% | 83.3% | 9.2s |
| **Multi Agent RAG** | 66.7% | 66.7% | 75.0% | 8.6s |

### 🏆 En İyi: Single Agent (66.7%)

---

## 📈 Component Matching

| Pipeline | SELECT | FROM | WHERE | GROUP BY |
|----------|--------|------|-------|----------|
| Single Agent | 100% | 33% | 67% | 67% |
| Multi Agent | 100% | 100% | 67% | 67% |
| Multi Agent RAG | 100% | 67% | 67% | 67% |

---

## 📝 Detailed Results

### Q1 🟢
**How many available features are there in total?**
```sql
-- Gold: SELECT count(*) FROM Other_Available_Features
```
- **Single_Agent** ✅: `SELECT COUNT(DISTINCT T2.feature_id) FROM Ref_Feature_Types ...`
- **Multi_Agent** ✅: `SELECT COUNT(*) FROM Other_Available_Features;...`
- **Multi_Agent_RAG** ✅: `SELECT COUNT(*) FROM Other_Available_Features;...`

### Q2 🟡
**What is the feature type name of feature AirCon?**
```sql
-- Gold: SELECT T2.feature_type_name FROM Other_Available_Features AS T1 JOIN Ref_Feature_Types AS T2 ON T1.feature_type_code  =  T2.feature_type_code WHERE T1.feature_name  =  "AirCon"
```
- **Single_Agent** ❌: `SELECT T2.feature_type_name 
FROM Other_Property_Features OP...`
- **Multi_Agent** ✅: `SELECT ft.feature_type_name FROM Ref_Feature_Types AS ft JOI...`
- **Multi_Agent_RAG** ❌: `SELECT feature_type_name FROM Ref_Feature_Types WHERE featur...`

### Q3 🟡
**Show the property type descriptions of properties belonging to that code.**
```sql
-- Gold: SELECT T2.property_type_description FROM Properties AS T1 JOIN Ref_Property_Types AS T2 ON T1.property_type_code  =  T2.property_type_code GROUP BY T1.property_type_code
```
- **Single_Agent** ✅: `SELECT RPT.property_type_description 
FROM Ref_Property_Type...`
- **Multi_Agent** ❌: `SELECT p.property_type_description FROM Properties AS p JOIN...`
- **Multi_Agent_RAG** ✅: `SELECT c.property_type_description FROM Properties AS p JOIN...`
