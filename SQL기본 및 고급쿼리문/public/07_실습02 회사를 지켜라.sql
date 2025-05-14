-- 01. 건강상태가 나빠진 원인 찾아보기
SELECT *
FROM env_cond;


-- 02. 조류독감이 의심되는 닭 찾아보기
SELECT 
    chick_no,
    check_date,
    weight,
    body_temp,
    breath_rate,
    feed_intake,
    diarrhea_yn,
    note
FROM health_cond
WHERE check_date = '2023-01-30'
  AND (
        body_temp >= 45
        OR breath_rate >= 80
        OR diarrhea_yn = 'Y'
      );


-- 03. 품종별 가장 무거운 닭 Top 3를 골라보기
SELECT
    a.chick_no,
    a.breeds,
    b.raw_weight
FROM chick_info a,
     prod_result b
WHERE a.chick_no = b.chick_no;

SELECT *
FROM (
    SELECT 
        c.chick_no,
        c.breeds,
        h.weight,
        ROW_NUMBER() OVER (PARTITION BY c.breeds ORDER BY h.weight DESC) AS rank
    FROM chick_info c
    JOIN health_cond h ON c.chick_no = h.chick_no
    WHERE h.check_date = '2023-01-30'
) sub
WHERE rank <= 3
ORDER BY breeds, rank;



-- 04. 여러 테이블의 데이터를 연결해 종합실적을 조회하기
SELECT
    a.chick_no AS 육계번호,
    (
        SELECT m.code_desc AS 품종
        FROM master_code m
        WHERE m.column_nm = 'breeds'
          AND m.code = a.breeds
    ),
    a.egg_weight || (
        SELECT u.unit
        FROM unit u
        WHERE u.column_nm = 'egg_weight'
    ) AS 종란무게,
    b.body_temp || (
        SELECT u.unit
        FROM unit u
        WHERE u.column_nm = 'body_temp'
    ) AS 체온,
    b.breath_rate || (
        SELECT u.unit
        FROM unit u
        WHERE u.column_nm = 'breath_rate'
    ) AS 호흡수,
    c.size_stand AS 호수,
    (
        SELECT m.code_desc AS 부적합여부
        FROM master_code m
        WHERE m.column_nm = 'pass_fail'
          AND m.code = c.pass_fail
    ),
    d.order_no AS 주문번호,
    d.customer AS 고객사,
    d.arrival_date AS 도착일,
    d.destination AS 도착지
FROM chick_info a
LEFT OUTER JOIN health_cond b ON a.chick_no = b.chick_no
LEFT OUTER JOIN prod_result c ON a.chick_no = c.chick_no
LEFT OUTER JOIN ship_result d ON a.chick_no = d.chick_no
WHERE b.check_date = '2023-01-30';

-- 05. 종합실적을 뷰 테이블로 만들어보기
CREATE OR REPLACE VIEW total_result AS
SELECT 
    a.chick_no AS "육계번호",
    (SELECT m.code_desc 
     FROM master_code m 
     WHERE m.column_nm::text = 'breeds'::text AND m.code::bpchar = a.breeds) AS "품종",
    a.egg_weight || (
        (SELECT u.unit 
         FROM unit u 
         WHERE u.column_nm::text = 'egg_weight'::text)::text) AS "종란무게",
    b.body_temp || (
        (SELECT u.unit 
         FROM unit u 
         WHERE u.column_nm::text = 'body_temp'::text)::text) AS "체온",
    b.breath_rate || (
        (SELECT u.unit 
         FROM unit u 
         WHERE u.column_nm::text = 'breath_rate'::text)::text) AS "호흡수",
    c.size_stand AS "호수",
    (SELECT m.code_desc 
     FROM master_code m 
     WHERE m.column_nm::text = 'pass_fail'::text AND m.code::bpchar = c.pass_fail) AS "부적합여부",
    d.order_no AS "주문번호",
    d.customer AS "고객사",
    d.arrival_date AS "도착일",
    d.destination AS "도착지"
FROM chick_info a
LEFT JOIN health_cond b ON a.chick_no = b.chick_no
LEFT JOIN prod_result c ON a.chick_no = c.chick_no
LEFT JOIN ship_result d ON a.chick_no = d.chick_no
WHERE b.check_date = '2023-01-30'::date;

-- 06. 뷰 속성 설정
ALTER TABLE total_result OWNER TO postgres;
COMMENT ON VIEW total_result IS '종합실적';



-- 07. 건강체크 함수 만들기
CREATE OR REPLACE FUNCTION detect_unhealthy_chick(p_chick_no TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM health_cond
        WHERE chick_no = p_chick_no
          AND (
              body_temp >= 43 OR
              breath_rate >= 80 OR
              diarrhea_yn = 'Y'
          )
    );
END;
$$ LANGUAGE plpgsql;

SELECT detect_unhealthy_chick('B2300009');
