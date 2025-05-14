-- 1-1. 두 테이블을 데이터 열로 합치기 (JOIN)
SELECT 
    chick_no,
    unnest(array['body_temp', 'breath_rate', 'feed_intake']) AS
    a.raw_weight, 
    b.order_no, 
    b.customer
FROM prod_result a
INNER JOIN ship_result b
ON a.chick_no = b.chick_no;

-- 1-2. LEFT OUTER JOIN
SELECT 
    a.chick_no, 
    a.pass_fail, 
    a.raw_weight, 
    b.order_no, 
    b.customer
FROM prod_result a
LEFT OUTER JOIN ship_result b
ON a.chick_no = b.chick_no;

-- 1-2. 두 테이블을 데이터 행으로 합치기 (UNION)
(
    SELECT chick_no, gender, hatchday
    FROM chick_info
    WHERE farm = 'A'
    AND gender = 'F'
    AND hatchday = '2023-01-03'
)
UNION
(
    SELECT 'A2300021', 'F', '2023-01-05'
);

-- 2-1. 쿼리 안에 쿼리 넣기
SELECT avg(egg_weight) FROM chick_info;

SELECT chick_no, egg_weight
FROM chick_info
WHERE egg_weight > 66.75;

SELECT chick_no, egg_weight
FROM chick_info
WHERE egg_weight > (SELECT avg(egg_weight) FROM chick_info);

-- 2-1. 쿼리 안에 쿼리 넣기 2
SELECT 
    a.chick_no, 
    a.breeds, 
    b.code_desc "breeds_nm"
FROM chick_info a, master_code b
WHERE 
    a.breeds = b.code
    AND b.column_nm = 'breeds';

-- 2-1. 쿼리 안에 쿼리 넣기 3
SELECT 
    a.chick_no, 
    a.breeds, 
    (
        SELECT m.code_desc "breeds_nm"
        FROM master_code m
        WHERE 
            m.column_nm = 'breeds'
            AND m.code = a.breeds
    )
FROM chick_info a;

-- 2-1. 쿼리 안에 쿼리 넣기 4
SELECT 
    a.chick_no, 
    a.breeds, 
    b.breeds_nm
FROM chick_info a, 
(
    SELECT code, code_desc "breeds_nm"
    FROM master_code
    WHERE column_nm = 'breeds'
) b
WHERE a.breeds = b.code;

-- 2-2. 나만의 뷰 테이블 만들기 (VIEW)
CREATE OR REPLACE VIEW breeds_prod
(
    prod_date, breeds_nm, total_sum
)
AS
SELECT 
    a.prod_date,
    (
        SELECT m.code_desc "breeds_nm"
        FROM master_code m
        WHERE m.column_nm = 'breeds'
        AND m.code = b.breeds
    ),
    sum(a.raw_weight) "total_sum"
FROM 
    prod_result a,
    chick_info b
WHERE 
    a.chick_no = b.chick_no
    AND a.pass_fail = 'P'
GROUP BY 
    a.prod_date, b.breeds;

SELECT * FROM breeds_prod;

-- 3-1. 행을 열로 바꾸기(PIVOT)
-- ① 부화일자, 성별 기준 마리 수 집계
SELECT hatchday, gender, count(chick_no)::int AS cnt
FROM chick_info
GROUP BY hatchday, gender
ORDER BY hatchday, gender;

-- ② 부화일자 기준 성별을 열로 변경
SELECT 
    a.hatchday,
    CASE WHEN a.gender = 'M' THEN a.cnt ELSE 0 END "Male",
    CASE WHEN a.gender = 'F' THEN a.cnt ELSE 0 END "Female"
FROM
(
    SELECT hatchday, gender, count(chick_no)::int AS cnt
    FROM chick_info
    GROUP BY hatchday, gender
    ORDER BY hatchday, gender
) a;

-- ③ 부화일자 기준 마리 수 합계
SELECT 
    a.hatchday,
    SUM(CASE WHEN a.gender = 'M' THEN a.cnt ELSE 0 END) "Male",
    SUM(CASE WHEN a.gender = 'F' THEN a.cnt ELSE 0 END) "Female"
FROM
(
    SELECT hatchday, gender, count(chick_no)::int AS cnt
    FROM chick_info
    GROUP BY hatchday, gender
    ORDER BY hatchday, gender
) a
GROUP BY a.hatchday;

-- ③ 부화일자 기준 마리 수 합계 2
CREATE EXTENSION tablefunc;
SELECT *
FROM crosstab
(
    'SELECT hatchday, gender, count(chick_no)::int AS cnt
     FROM chick_info
     GROUP BY hatchday, gender
     ORDER BY hatchday, gender DESC'
) AS pivot_r(hatchday date, "Male" int, "Female" int);

-- 3-2. 열을 행으로 바꾸기(UNPIVOT)
SELECT chick_no, body_temp, breath_rate, feed_intake
FROM health_cond
WHERE check_date = '2023-01-20'
AND chick_no LIKE 'A%';

-- 3-2. 열을 행으로 바꾸기(UNPIVOT) 2
SELECT a.chick_no, a.health, a.cond
FROM
(
    SELECT chick_no, 'body_temp' AS health, body_temp AS cond
    FROM health_cond
    WHERE check_date = '2023-01-20' AND chick_no LIKE 'A%'
    UNION
    SELECT chick_no, 'breath_rate' AS health, breath_rate AS cond
    FROM health_cond
    WHERE check_date = '2023-01-20' AND chick_no LIKE 'A%'
    UNION
    SELECT chick_no, 'feed_intake' AS health, feed_intake AS cond
    FROM health_cond
    WHERE check_date = '2023-01-20' AND chick_no LIKE 'A%'
) a
ORDER BY a.chick_no, a.health;

-- 3-2. 열을 행으로 바꾸기(UNPIVOT) 3
SELECT 
    chick_no,
    unnest(array['body_temp', 'breath_rate', 'feed_intake']) AS health,
    unnest(array[body_temp, breath_rate, feed_intake]) AS cond
FROM health_cond
WHERE check_date = '2023-01-20'
AND chick_no LIKE 'A%'
ORDER BY chick_no, health;

SELECT 
    chick_no,
    unnest(array['body_temp', 'breath_rate', 'feed_intake']) AS health,
    unnest(array[body_temp, breath_rate, feed_intake]) AS cond
FROM health_cond
ORDER BY chick_no, health;

-- 도전미션
-- 1. prod_result, chick_info 생산 결과와 병아리 정보 조인하여 성별별 평균 중량 구하기
SELECT 
    c.gender, 
    AVG(p.raw_weight) AS avg_weight
FROM prod_result p
INNER JOIN chick_info c
ON p.chick_no = c.chick_no
GROUP BY c.gender
ORDER BY c.gender;

-- 2. 건강 상태에서 설사(diarrhea_yn = 'Y')가 있었던 병아리 리스트
SELECT 
    h.chick_no, 
    c.farm, 
    h.check_date
FROM health_cond h
INNER JOIN chick_info c
ON h.chick_no = c.chick_no
WHERE h.diarrhea_yn = 'Y'
ORDER BY h.check_date DESC, h.chick_no;