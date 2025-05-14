-- 1-2. 전체 데이터 조회하기
SELECT * 
FROM chick_info;

-- 1-3. 전체 데이터 개수 출력하기
SELECT COUNT(*) 
FROM chick_info;

-- 1-4. 원하는 열만 조회하기
SELECT chick_no, hatchday, egg_weight 
FROM chick_info;

-- 1-5. 열 이름 바꿔 조회하기
SELECT chick_no AS cn, hatchday AS "부화일자" 
FROM chick_info;

-- 1-6. 데이터 정렬하기 (ORDER BY)
SELECT chick_no, hatchday, egg_weight 
FROM chick_info 
ORDER BY egg_weight;

SELECT chick_no, hatchday, egg_weight 
FROM chick_info 
ORDER BY egg_weight DESC;

SELECT chick_no, hatchday, egg_weight 
FROM chick_info 
ORDER BY egg_weight DESC, hatchday ASC, chick_no ASC;

-- 1-7. 원하는 개수의 데이터만 조회하기 (LIMIT, OFFSET)
SELECT chick_no AS cn, hatchday AS "부화날짜", egg_weight
FROM chick_info
ORDER BY egg_weight DESC, "부화날짜" ASC
LIMIT 7;

SELECT chick_no, hatchday, egg_weight 
FROM chick_info 
ORDER BY egg_weight DESC, hatchday ASC, chick_no ASC 
LIMIT 4 OFFSET 1;

-- 1-8. 중복된 결과 제거하기 (DISTINCT)
SELECT DISTINCT(hatchday) 
FROM chick_info;

-- 1-9. 원하는 조건의 데이터만 조회하기 (WHERE)
SELECT * 
FROM chick_info 
WHERE gender = 'M';

SELECT * 
FROM chick_info 
WHERE egg_weight >= 70;

SELECT * 
FROM chick_info 
WHERE hatchday BETWEEN '2023-01-01' AND '2023-01-02';

SELECT * 
FROM chick_info 
WHERE egg_weight > 69 OR egg_weight <= 62;

SELECT * 
FROM chick_info 
WHERE breeds LIKE 'D%';

SELECT * 
FROM ship_result
WHERE destination IN ('부산', '울산');

-- 1-10. 원하는 문자만 가져오기 (SUBSTRING)
SELECT chick_no, 
    LEFT(chick_no, 1), 
    SUBSTRING(chick_no, 2, 3), 
    RIGHT(chick_no, 4) 
FROM chick_info 
LIMIT 5;

-- 1-11. 기타 문자열 함수
SELECT LENGTH(chick_no) 
FROM chick_info 
LIMIT 5;

SELECT farm || gender || breeds AS fgb 
FROM chick_info 
LIMIT 5;

SELECT LOWER(gender) 
FROM chick_info 
LIMIT 5;

SELECT REPLACE(gender, 'M', 'Male') 
FROM chick_info 
LIMIT 5;

-- 성별 컬럼의 글자를 소문자(대문자)로 변경하기
UPDATE chick_info
SET gender = UPPER(gender);

-- chick_no 분해
SELECT chick_no, 
    CASE 
        WHEN LEFT(chick_no, 1) = 'A' THEN 'A'
        WHEN LEFT(chick_no, 1) = 'B' THEN 'B'
        ELSE 'Unknown'
    END AS 사육장,
    SUBSTRING(chick_no, 2, 2) AS 출생연도,
    CASE 
        WHEN SUBSTRING(chick_no, 4, 1) = '0' THEN 'M'
        WHEN SUBSTRING(chick_no, 4, 1) = '1' THEN 'F'
        ELSE 'Unknown'
    END AS 성별,
    CASE 
        WHEN LEFT(chick_no, 1) = 'A' THEN 'A'
        WHEN LEFT(chick_no, 1) = 'B' THEN 'B'
        ELSE 'Unknown'
    END || SUBSTRING(chick_no, 2, 2) || 
    CASE 
        WHEN SUBSTRING(chick_no, 4, 1) = '0' THEN 'M'
        WHEN SUBSTRING(chick_no, 4, 1) = '1' THEN 'F'
        ELSE 'Unknown'
    END AS 파생변수
FROM chick_info;
