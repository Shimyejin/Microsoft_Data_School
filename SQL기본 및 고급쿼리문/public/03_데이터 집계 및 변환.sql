-- 2-1. 데이터 집계하기 (GROUP BY)
-- ① 생산실적 테이블에서 생산일자별 생닭중량 합계 조회하기
SELECT prod_date, SUM(raw_weight) AS prod
FROM prod_result
GROUP BY prod_date;

SELECT prod_date, AVG(raw_weight) AS prod
FROM prod_result
GROUP BY prod_date;

SELECT prod_date, COUNT(chick_no) AS cnt
FROM prod_result
GROUP BY prod_date;

-- ② 출하실적 테이블에서 고객사별 출하 마릿수 조회하기

SELECT customer, COUNT(chick_no) AS cnt
FROM ship_result
GROUP BY customer;

-- 2-2. 원하는 조건으로 데이터 집계하기 (HAVING)
SELECT customer, COUNT(chick_no) AS cnt
FROM ship_result
GROUP BY customer
HAVING COUNT(chick_no) >= 10;

-- ③ 출하실적 테이블에서 2023년 2월 4일 이후 고객사별 납품된 마릿수 조회하기
SELECT customer, COUNT(chick_no) AS cnt
FROM ship_result
WHERE arrival_date > '2023-02-04'

SELECT customer, COUNT(chick_no) AS cnt
FROM ship_result
WHERE arrival_date > '2023-02-04'
GROUP BY customer
HAVING COUNT(chick_no) >= 7
ORDER BY cnt DESC;

-- 3-1. 데이터 타입 변환하기 (TO_CHAR)
SELECT hatchday, TO_CHAR(hatchday, 'Mon')
FROM chick_info
LIMIT 5;

-- 3-2. NULL 변환 (COALESCE, NULLIF)
SELECT farm, date, humid, COALESCE(humid, 60)
FROM env_cond
WHERE date BETWEEN '2023-01-23' AND '2023-01-27'
AND farm = 'A';

SELECT farm, date, humid, NULLIF(humid, 60)
FROM env_cond
WHERE date BETWEEN '2023-01-23' AND '2023-01-27'
AND farm = 'A';

-- 3-3. 원하는 조건으로 항목 추가하기 (CASE)
SELECT chick_no,
    egg_weight,
    CASE
        WHEN egg_weight > 69 THEN 'H'
        WHEN egg_weight > 65 THEN 'M'
        ELSE 'L'
    END AS "w_grade"
FROM chick_info
LIMIT 10;

-- 도전미션
-- 1. chick_info 테이블에서 종란 무게가 가장 높은 상위 5개의 데이터를 조회하세요.
SELECT *
FROM chick_info
ORDER BY egg_weight DESC
LIMIT 5;

-- 2. health_cond 기록 중 몸무게가 800g 초과이고 체온이 41도 미만인 병아리 조회
SELECT chick_no, check_date, weight, body_temp
FROM health_cond
WHERE weight > 800 AND body_temp < 41
ORDER BY weight;

-- 3. chick_info 테이블에서 부화일자별로 육계의 수를 조회하되, 10마리 이상인 경우만 조회
SELECT hatchday, COUNT(*) AS count
FROM chick_info
GROUP BY hatchday
HAVING COUNT(*) >= 10
ORDER BY hatchday;

-- 4. 농장별 조도(lux)가 10 이상 측정된 일자 수
SELECT farm, COUNT(DISTINCT date) AS high_lux_days
FROM env_cond
WHERE lux >= 10
GROUP BY farm;

-- 5. health_cond 테이블에서 노트가 없는 경우 '없음'으로 표시하여 조회
SELECT chick_no, 
    CASE
        WHEN note IS NULL THEN '없음'
        ELSE note
    END AS note
FROM health_cond;

-- 6. chick_info 테이블에서 평균 종란 무게보다 높은 육계를 조회
SELECT *
FROM chick_info
WHERE egg_weight > (SELECT AVG(egg_weight) FROM chick_info);

-- 7. 생산 합격 여부(pass_fail)를 기준으로 상태 분류
SELECT chick_no, prod_date,
    CASE
        WHEN pass_fail = 'P' THEN '합격'
        WHEN pass_fail = 'F' THEN '불합격'
        ELSE '미확인'
    END AS result_status
FROM prod_result;

-- 8. ship_result 테이블을 사용하여 고객사별 출하 주문 건수를 3단계 계층으로 분류
-- 10건 이상: 'A등급'
-- 5-9건: 'B등급'
-- 5건 미만: 'C등급'
SELECT customer, COUNT(chick_no) AS cnt,
    CASE
        WHEN COUNT(chick_no) >= 10 THEN 'A등급'
        WHEN COUNT(chick_no) >= 5 THEN 'B등급'
        ELSE 'C등급'
    END AS grade
FROM ship_result
GROUP BY customer;