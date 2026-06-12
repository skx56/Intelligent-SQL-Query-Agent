"""
Analyzes Spider questions by difficulty level
Easy: Simple SELECT, COUNT (no JOIN, no subquery)
Medium: 1 JOIN or GROUP BY
Hard: Multiple JOINs, subquery, HAVING
"""
import json

data = json.load(open('data/spider_data/spider_data/dev.json', encoding='utf-8'))

def estimate_hardness(query):
    """Estimate difficulty from SQL query"""
    q = query.upper()
    
    join_count = q.count(' JOIN ')
    has_subquery = 'SELECT' in q[q.find('FROM'):] if 'FROM' in q else False
    has_group = 'GROUP BY' in q
    has_having = 'HAVING' in q
    has_union = 'UNION' in q or 'INTERSECT' in q or 'EXCEPT' in q
    
    # Calculate difficulty
    if has_union or has_subquery or join_count >= 2 or has_having:
        return 'hard'
    elif join_count == 1 or has_group:
        return 'medium'
    else:
        return 'easy'

# Difficulty distribution for each DB
db_stats = {}
for d in data:
    db = d['db_id']
    h = estimate_hardness(d['query'])
    if db not in db_stats:
        db_stats[db] = {'easy': 0, 'medium': 0, 'hard': 0, 'total': 0}
    db_stats[db][h] += 1
    db_stats[db]['total'] += 1

# Show databases with most easy+medium questions
print('=' * 75)
print('DATABASE DIFFICULTY ANALYSIS')
print('=' * 75)
print(f"{'Database':<26} | {'Easy':>5} | {'Medium':>6} | {'Hard':>5} | {'Total':>5}")
print('-' * 75)

sorted_dbs = sorted(db_stats.items(), key=lambda x: x[1]['easy'] + x[1]['medium'], reverse=True)
for db, stats in sorted_dbs[:15]:
    print(f"{db:<26} | {stats['easy']:>5} | {stats['medium']:>6} | {stats['hard']:>5} | {stats['total']:>5}")

print('=' * 75)
print("\n🎯 RECOMMENDED DATABASES (Many easy+medium):")
for db, stats in sorted_dbs[:5]:
    easy_med = stats['easy'] + stats['medium']
    print(f"  • {db}: {easy_med} easy/medium questions ({stats['easy']} easy, {stats['medium']} medium)")
