-- 01. 기본 조회: chick_info 테이브르이 모든 데이터 조회
SELECT * FROM chick_info;

-- 02. 조건 필터링: 성별이 암컷(F)인 병아리 정보 조회
SELECT * FROM chick_info
WHERE gender = 'F';

-- 03. 정렬 및 제한: 계란 무게(egg_weight)가 68g 이상인 데이터를 무거운 순으로 7개 출력
SELECT * FROM chick_info
WHERE egg_weight >= 68
ORDER BY egg_weight DESC
LIMIT 7;

-- 04. 날짜 범위: 2023-01-01 ~ 2023-01-02 사이에 부화한 병아리 조회
SELECT * FROM chick_info
WHERE hatchday BETWEEN '2023-01-01' AND '2023-01-02';

-- 05. NULL 처리: env_cond 테이블에서 습도(humid)가 NULL인 레코드 조회
SELECT * FROM env_cond
WHERE humid IS NULL;

-- 06. 패턴 검색: 품종(breeds)이 'C'로 시작하는 병아리 조회
SELECT * FROM chick_info
WHERE breeds LIKE 'C%';

-- 07. 조인 활용: chick_info와 health_cond를 조인해 2023-01-30 건강검진 데이터 조회
SELECT *
FROM chick_info c
JOIN health_cond h ON c.chick_no = h.chick_no
WHERE h.check_date = '2023-01-30';

-- 08. 집계 함수: 농장(farm)별 평균 계란 무게(egg_weight) 조회
SELECT farm, AVG(egg_weight) AS avg_weight
FROM chick_info
GROUP BY farm;

-- 09. 그룹 필터링: 고객사(customer)별 출하량이 10마리 이상인 데이터 조회
SELECT customer, COUNT(*) AS count
FROM ship_result
GROUP BY customer
HAVING COUNT(*) >= 10;

-- 10. 서브쿼리: 평균 계란 무게보다 큰 병아리 조회
SELECT *
FROM chick_info
WHERE egg_weight > (
  SELECT AVG(egg_weight) FROM chick_info
);

-- 11. CASE 문: 생닭 무게(raw_weight) 기준 등급 분류
SELECT chick_no, raw_weight,
  CASE
    WHEN raw_weight < 1000 THEN 'S'
    WHEN raw_weight < 1100 THEN 'M'
    ELSE 'L'
  END AS weight_grade
FROM prod_result;

-- 12. UNION: A농장과 B농장의 암컷 병아리 데이터 통합 조회
SELECT * FROM chick_info
WHERE gender = 'M' AND farm = 'A'
UNION
SELECT * FROM chick_info
WHERE gender = 'F' AND farm = 'B';

-- 13. 날짜 함수: 부화일(hatchday)을 'YYYY년 MM월 DD일' 형식으로 출력
SELECT chick_no,
  TO_CHAR(hatchday, 'YYYY"년" MM"월" DD"일"') AS formatted_hatchday
FROM chick_info;

-- 14. 복합 조인: chick_info, prod_result, ship_result를 조인하여 부산으로 출하된 생닭 정보 조회
SELECT *
FROM chick_info c
JOIN prod_result p ON c.chick_no = p.chick_no
JOIN ship_result s ON c.chick_no = s.chick_no
WHERE s.destination = '부산';

-- 15. 뷰 생성: 품종별 주간 생산량 집계 뷰 생성
CREATE VIEW weekly_production_summary AS
SELECT c.breeds,
       COUNT(*) AS total,
       ROUND(AVG(p.raw_weight), 1) AS avg_weight
FROM chick_info c
JOIN prod_result p ON c.chick_no = p.chick_no
GROUP BY c.breeds;

-- 16. 문자열 함수: chick_no에서 첫 글자(A/B)를 농장명으로 변환해 출력
SELECT chick_no,
       CASE
         WHEN LEFT(chick_no, 1) = 'A' THEN 'A농장'
         WHEN LEFT(chick_no, 1) = 'B' THEN 'B농장'
         ELSE '기타'
       END AS farm_name
FROM chick_info;

-- 17. 복합 쿼리: 2023-01-30 기준 체온 + 호흡수 + 사료섭취량으로 건강 상태 판단
SELECT chick_no,
       CASE
         WHEN body_temp > 45 THEN '위험'
         WHEN body_temp > 41 THEN '주의'
         ELSE '정상'
       END AS status
FROM health_cond
WHERE check_date = '2023-01-30';

-- 18. 병아리 생산 합격률 계산
SELECT c.farm,
       ROUND(100.0 * SUM(CASE WHEN p.pass_fail = 'P' THEN 1 ELSE 0 END) / COUNT(*)) AS pass_rate
FROM chick_info c
JOIN prod_result p ON c.chick_no = p.chick_no
GROUP BY c.farm;

-- 19. 조인 + 뷰: 특정 농장 생산 합격 생닭 제품의 출하 목적지 별 합계 보기
CREATE VIEW view_farm_ship_summary AS
SELECT ci.farm,
       sr.customer,
       COUNT(*) AS shipped_count
FROM chick_info ci
JOIN prod_result pr ON ci.chick_no = pr.chick_no
JOIN ship_result sr ON ci.chick_no = sr.chick_no
WHERE pr.pass_fail = 'P'
GROUP BY ci.farm, sr.customer;

SELECT *
FROM view_farm_ship_summary
WHERE farm = 'A';

-- 20. 날짜별 농장별 생산 마릿수 시각화
-- prod_date, farm별 마릿수를 집계
-- 농장명을 열(column)로 전환 > 피벗 처리
SELECT pr.prod_date, ci.farm, COUNT(*) AS prod_count
FROM prod_result pr
JOIN chick_info ci ON pr.chick_no = ci.chick_no
GROUP BY pr.prod_date, ci.farm
ORDER BY pr.prod_date, ci.farm;

SELECT pr.prod_date,
       SUM(CASE WHEN ci.farm = 'A' THEN 1 ELSE 0 END) AS "Farm A",
       SUM(CASE WHEN ci.farm = 'B' THEN 1 ELSE 0 END) AS "Farm B",
       SUM(CASE WHEN ci.farm = 'C' THEN 1 ELSE 0 END) AS "Farm C"
FROM prod_result pr
JOIN chick_info ci ON pr.chick_no = ci.chick_no
GROUP BY pr.prod_date
ORDER BY pr.prod_date;
