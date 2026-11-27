-- Run with sqlite3 data/processed/analysis.sqlite < Scripts/core_queries.sql
-- SQL tables are documented aggregates, NOT raw event rows.
-- 1. Period user metrics, independently recomputed from one row per user.
SELECT COUNT(*) AS uv, SUM(pv) AS pv, SUM(pv>0) AS browse_uv,
 SUM(fav>0) AS favorite_users, SUM(cart>0) AS cart_users, SUM(buy>0) AS buyers,
 1.0*SUM(buy>0)/COUNT(*) AS purchase_rate FROM users;
-- 2. Daily activity and buyer coverage (users are deduplicated inside each day).
SELECT date, uv AS dau, pv, buy_uv, 1.0*buy_uv/NULLIF(uv,0) AS purchase_rate FROM daily ORDER BY day;
-- 3. Exact-day retention. Right-censored cells remain NULL.
SELECT cohort_date,cohort_users,offset,retained_users,retention_rate
FROM cohort WHERE offset IN (1,3,7) ORDER BY cohort_date,offset;
-- 4. Four quadrants. This is a descriptive whole-window segmentation.
SELECT segment,COUNT(*) AS users,AVG(active_days) AS active_days,AVG(purchase_days) AS purchase_days
FROM users GROUP BY segment;
-- 5. Pair-level 24h conversion (computed by timestamp matching in 01_analyze.py).
SELECT behavior,eligible_pairs,converted_pairs,1.0*converted_pairs/NULLIF(eligible_pairs,0) AS rate FROM conversion;
-- 6. Priority item candidates: no causal diagnosis is implied.
SELECT item_id,pv_uv,eligible_pairs,converted_pairs,conversion_rate FROM item_opportunities ORDER BY pv_uv DESC LIMIT 20;
