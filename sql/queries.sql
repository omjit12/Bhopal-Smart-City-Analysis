-- Q1. Which Smart City projects are completed vs pending?
SELECT 
    status,
    COUNT(*) AS total_projects,
    ROUND(SUM(budget_cr), 2) AS total_budget_cr,
    ROUND(SUM(spent_cr), 2) AS total_spent_cr,
    ROUND(AVG(budget_utilization) * 100, 2) AS avg_utilization_pct
FROM smart_city_projects
GROUP BY status
ORDER BY total_projects DESC;

-- Q2. Which zones received the highest Smart City investment?
SELECT 
    zone,
    COUNT(*) AS total_projects,
    ROUND(SUM(budget_cr), 2) AS total_budget_cr,
    ROUND(SUM(spent_cr), 2) AS total_spent_cr,
    COUNT(CASE WHEN status = 'Completed' THEN 1 END) AS completed,
    COUNT(CASE WHEN status = 'Delayed' THEN 1 END) AS delayed
FROM smart_city_projects
GROUP BY zone
ORDER BY total_budget_cr DESC;

-- Q3. Which project categories have the worst delivery record?
SELECT 
    category,
    COUNT(*) AS total,
    COUNT(CASE WHEN status = 'Completed' THEN 1 END) AS completed,
    COUNT(CASE WHEN status = 'Delayed' THEN 1 END) AS delayed,
    ROUND(COUNT(CASE WHEN status = 'Delayed' THEN 1 END) * 100.0 / COUNT(*), 2) AS delay_rate_pct
FROM smart_city_projects
GROUP BY category
ORDER BY delay_rate_pct DESC;

-- 💧 Module 2 — Lakes & Environment
-- Q4. How has Upper Lake vs Lower Lake water quality compared year on year?

SELECT 
    lake_name,
    year_num,
    ROUND(AVG(dissolved_oxygen), 2) AS avg_do,
    ROUND(AVG(bod), 2) AS avg_bod,
    ROUND(AVG(ph_value), 2) AS avg_ph,
    COUNT(CASE WHEN pollution_flag = 'Heavily Polluted' THEN 1 END) AS heavily_polluted_months
FROM lake_quality
GROUP BY lake_name, year_num
ORDER BY lake_name, year_num;

-- Q5. Which months are worst for Bhopal AQI?
SELECT 
    month_num,
    TO_CHAR(TO_DATE(month_num::TEXT, 'MM'), 'Month') AS month_name,
    ROUND(AVG(aqi_value), 0) AS avg_aqi,
    ROUND(AVG(pm25), 2) AS avg_pm25,
    ROUND(AVG(pm10), 2) AS avg_pm10,
    COUNT(CASE WHEN health_flag = 'Unhealthy' THEN 1 END) AS unhealthy_days
FROM air_quality
GROUP BY month_num
ORDER BY avg_aqi DESC;

-- Q6. How has Bhopal AQI trended year over year?
SELECT 
    year_num,
    season,
    ROUND(AVG(aqi_value), 0) AS avg_aqi,
    COUNT(CASE WHEN health_flag = 'Unhealthy' THEN 1 END) AS unhealthy_days,
    COUNT(CASE WHEN health_flag = 'Healthy' THEN 1 END) AS healthy_days
FROM air_quality
GROUP BY year_num, season
ORDER BY year_num, 
    CASE season 
        WHEN 'Winter' THEN 1 
        WHEN 'Summer' THEN 2 
        WHEN 'Monsoon' THEN 3 
        ELSE 4 
    END;

-- 🏥 Module 3 — Healthcare
-- Q7. Which wards have the lowest hospital beds per 1000 population?

SELECT 
    w.ward_name,
    w.zone,
    w.population,
    COUNT(h.facility_id) AS total_facilities,
    COALESCE(SUM(h.beds), 0) AS total_beds,
    ROUND(COALESCE(SUM(h.beds), 0) * 1000.0 / w.population, 2) AS beds_per_1000,
    RANK() OVER (ORDER BY COALESCE(SUM(h.beds), 0) * 1000.0 / w.population) AS underserved_rank
FROM wards w
LEFT JOIN healthcare h ON w.ward_id = h.ward_id
GROUP BY w.ward_id, w.ward_name, w.zone, w.population
ORDER BY beds_per_1000 ASC
LIMIT 10;

-- Q8. Old Bhopal vs New Bhopal — healthcare gap analysis
SELECT 
    w.zone,
    SUM(w.population) AS total_population,
    COUNT(h.facility_id) AS total_facilities,
    COALESCE(SUM(h.beds), 0) AS total_beds,
    ROUND(COUNT(h.facility_id) * 1000.0 / SUM(w.population), 4) AS facilities_per_1000,
    ROUND(COALESCE(SUM(h.beds), 0) * 1000.0 / SUM(w.population), 4) AS beds_per_1000
FROM wards w
LEFT JOIN healthcare h ON w.ward_id = h.ward_id
GROUP BY w.zone
ORDER BY beds_per_1000 ASC;

-- Q9. Which facility types are most lacking across zones?
SELECT 
    w.zone,
    h.facility_type,
    COUNT(*) AS total,
    SUM(h.beds) AS total_beds
FROM healthcare h
JOIN wards w ON h.ward_id = w.ward_id
GROUP BY w.zone, h.facility_type
ORDER BY w.zone, h.facility_type;

-- 📋 Module 4 — Citizen Grievances
-- Q10. Which wards generate the most complaints?
SELECT 
    c.ward_name,
    c.zone,
    COUNT(*) AS total_complaints,
    COUNT(CASE WHEN status = 'Pending' THEN 1 END) AS pending,
    COUNT(CASE WHEN status = 'Resolved' THEN 1 END) AS resolved,
    ROUND(COUNT(CASE WHEN status = 'Pending' THEN 1 END) * 100.0 / COUNT(*), 2) AS pending_pct,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS complaint_rank
FROM complaints c
GROUP BY c.ward_name, c.zone
ORDER BY total_complaints DESC
LIMIT 10;

-- Q11. Which complaint categories take longest to resolve?

SELECT 
    category,
    COUNT(*) AS total_complaints,
    ROUND(AVG(days_to_resolve), 1) AS avg_days_to_resolve,
    MIN(days_to_resolve) AS fastest_resolved,
    MAX(days_to_resolve) AS slowest_resolved,
    COUNT(CASE WHEN status = 'Pending' THEN 1 END) AS still_pending
FROM complaints
WHERE days_to_resolve IS NOT NULL
GROUP BY category
ORDER BY avg_days_to_resolve DESC;

-- Q12. Which zones have the worst resolution rates?

SELECT 
    zone,
    COUNT(*) AS total_complaints,
    COUNT(CASE WHEN status = 'Resolved' THEN 1 END) AS resolved,
    COUNT(CASE WHEN status = 'Pending' THEN 1 END) AS pending,
    ROUND(COUNT(CASE WHEN status = 'Resolved' THEN 1 END) * 100.0 / COUNT(*), 2) AS resolution_rate_pct,
    ROUND(AVG(CASE WHEN days_to_resolve IS NOT NULL THEN days_to_resolve END), 1) AS avg_resolution_days
FROM complaints
GROUP BY zone
ORDER BY resolution_rate_pct ASC;

-- Q13. Has complaint resolution improved year over year?

SELECT 
    year,
    COUNT(*) AS total_complaints,
    COUNT(CASE WHEN status = 'Resolved' THEN 1 END) AS resolved,
    ROUND(COUNT(CASE WHEN status = 'Resolved' THEN 1 END) * 100.0 / COUNT(*), 2) AS resolution_rate_pct,
    ROUND(AVG(CASE WHEN days_to_resolve IS NOT NULL THEN days_to_resolve END), 1) AS avg_days,
    LAG(ROUND(COUNT(CASE WHEN status = 'Resolved' THEN 1 END) * 100.0 / COUNT(*), 2)) 
        OVER (ORDER BY year) AS prev_year_rate,
    ROUND(COUNT(CASE WHEN status = 'Resolved' THEN 1 END) * 100.0 / COUNT(*), 2) -
        LAG(ROUND(COUNT(CASE WHEN status = 'Resolved' THEN 1 END) * 100.0 / COUNT(*), 2)) 
        OVER (ORDER BY year) AS yoy_change
FROM complaints
GROUP BY year
ORDER BY year;

-- Q14. Which complaint categories are highest priority and most unresolved?
SELECT 
    category,
    complaint_priority,
    COUNT(*) AS total,
    COUNT(CASE WHEN status = 'Pending' THEN 1 END) AS unresolved,
    ROUND(COUNT(CASE WHEN status = 'Pending' THEN 1 END) * 100.0 / COUNT(*), 2) AS unresolved_pct,
    ROUND(AVG(CASE WHEN days_to_resolve IS NOT NULL THEN days_to_resolve END), 1) AS avg_resolution_days
FROM complaints
GROUP BY category, complaint_priority
ORDER BY complaint_priority, unresolved_pct DESC;

-- Q15. Overall City Health Score — combining all modules
WITH smart_city_score AS (
    SELECT 
        zone,
        ROUND(COUNT(CASE WHEN status = 'Completed' THEN 1 END) * 100.0 / COUNT(*), 2) AS project_completion_pct
    FROM smart_city_projects
    GROUP BY zone
),
healthcare_score AS (
    SELECT 
        w.zone,
        ROUND(SUM(h.beds) * 1000.0 / SUM(w.population), 4) AS beds_per_1000
    FROM wards w
    LEFT JOIN healthcare h ON w.ward_id = h.ward_id
    GROUP BY w.zone
),
complaint_score AS (
    SELECT 
        zone,
        ROUND(COUNT(CASE WHEN status = 'Resolved' THEN 1 END) * 100.0 / COUNT(*), 2) AS resolution_rate
    FROM complaints
    GROUP BY zone
)
SELECT 
    hs.zone,
    COALESCE(sc.project_completion_pct, 0) AS smart_city_score,
    ROUND(hs.beds_per_1000 * 100, 2) AS healthcare_score,
    cs.resolution_rate AS grievance_score,
    ROUND((COALESCE(sc.project_completion_pct, 0) + 
           ROUND(hs.beds_per_1000 * 100, 2) + 
           cs.resolution_rate) / 3, 2) AS overall_city_score
FROM healthcare_score hs
LEFT JOIN smart_city_score sc ON hs.zone = sc.zone
LEFT JOIN complaint_score cs ON hs.zone = cs.zone
ORDER BY overall_city_score DESC;