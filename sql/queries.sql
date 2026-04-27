-- Q1: Top Inventors
SELECT i.name AS inventor_name, COUNT(DISTINCT r.patent_id) AS patent_count
FROM relationships r
JOIN inventors i ON i.inventor_id = r.inventor_id
GROUP BY i.inventor_id, inventor_name
ORDER BY patent_count DESC, inventor_name ASC
LIMIT 10;


-- Q2: Top Companies
SELECT c.name AS company_name, COUNT(DISTINCT r.patent_id) AS patent_count
FROM relationships r
JOIN companies c ON c.company_id = r.company_id
GROUP BY c.company_id, company_name
ORDER BY patent_count DESC, company_name ASC
LIMIT 10;


-- Q3: Countries
SELECT i.country AS country, COUNT(DISTINCT r.patent_id) AS patent_count
FROM relationships r
JOIN inventors i ON i.inventor_id = r.inventor_id
GROUP BY i.country
ORDER BY patent_count DESC, country ASC;


-- Q4: Trends Over Time
SELECT year, COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year ASC;


-- Q5: JOIN Query (patents, inventors, companies)
SELECT p.patent_id, p.title, p.year,
       i.name AS inventor_name,
       c.name AS company_name
FROM relationships r
JOIN patents p ON p.patent_id = r.patent_id
JOIN inventors i ON i.inventor_id = r.inventor_id
JOIN companies c ON c.company_id = r.company_id
ORDER BY p.year DESC, p.patent_id ASC
LIMIT 100;


-- Q6: CTE Query (inventors with >=2 patents)
WITH inventor_counts AS (
    SELECT i.inventor_id, i.name AS inventor_name, COUNT(DISTINCT r.patent_id) AS patents
    FROM inventors i
    JOIN relationships r ON r.inventor_id = i.inventor_id
    GROUP BY i.inventor_id, inventor_name
)
SELECT inventor_name, patents
FROM inventor_counts
WHERE patents >= 2
ORDER BY patents DESC, inventor_name ASC
LIMIT 10;


-- Q7: Ranking Query (window function)
SELECT inventor_name, patent_count, patent_rank
FROM (
    SELECT
        i.name AS inventor_name,
        COUNT(DISTINCT r.patent_id) AS patent_count,
        RANK() OVER (ORDER BY COUNT(DISTINCT r.patent_id) DESC) AS patent_rank
    FROM relationships r
    JOIN inventors i ON i.inventor_id = r.inventor_id
    GROUP BY i.inventor_id, inventor_name
) ranked
ORDER BY patent_rank ASC, inventor_name ASC
LIMIT 10;
