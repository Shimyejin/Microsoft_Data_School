-- 함수 도전미션: 이전의 view를 함수로 변경
CREATE OR REPLACE FUNCTION get_farm_ship_summary(farm_code TEXT)
RETURNS TABLE (
  farm TEXT,
  customer TEXT,
  shipped_count INTEGER
)
AS $$
  SELECT ci.farm, sr.customer, COUNT(*) AS shipped_count
  FROM prod_result pr
  JOIN chick_info ci ON pr.chick_no = ci.chick_no
  JOIN ship_result sr ON pr.chick_no = sr.chick_no
  WHERE pr.pass_fail = 'P' AND ci.farm = farm_code
  GROUP BY ci.farm, sr.customer;
$$ LANGUAGE sql;

SELECT * 
FROM get_farm_ship_summary('A');

-- Procedure(프로시저)
CREATE TABLE breeds_prod_tbl(
    prod_date date NOT NULL,
    breeds_nm character(20) NOT NULL,
    total_sum bigint NOT NULL,
    save_time time without time zone NOT NULL
);

COMMENT ON TABLE breeds_prod_tbl IS '품종별 생산실적';

-- 1. 프로시저 만들기
CREATE OR REPLACE PROCEDURE breeds_prod_proc()
        LANGUAGE sql
AS $procedure$
    INSERT INTO breeds_prod_tbl(prod_date, breeds_nm, total_sum, save_time)
    (
        SELECT prod_date, breeds_nm, total_sum, CURRENT_TIME AS save_time
        FROM breeds_prod
        WHERE prod_date = '2023-01-31'
    );
$procedure$;

-- 2. 생성된 프로시저 실행
CALL breeds_prod_proc();

-- 3. 테이블의 내용 삭제하기
DELETE FROM breeds_prod_tbl;

-- Job(잡)
DO $$
DECLARE
    jid integer;
    scid integer;
BEGIN
    -- 1. Job 생성
    INSERT INTO pgagent.pga_job (
        jobjclid, jobname, jobdesc, jobhostagent, jobenabled
    ) VALUES (
        1, 'breeds_prod_job', '', '', true
    )
    RETURNING jobid INTO jid;

    -- 2. Step 정의
    INSERT INTO pgagent.pga_jobstep (
        jstjobid, jstname, jstenabled, jstkind,
        jstconnstr, jstdbname, jstonerror,
        jstcode, jstdesc
    )
    VALUES (
        jid, 'step', true, 's',
        'user=''postgres'' password=''1111'' host=''localhost'' port=''5432'' dbname=''chicken''',
        '', 'f',
        'CALL fms.breeds_prod_proc();',
        ''
    );

    -- 3. 스케줄 정의
    INSERT INTO pgagent.pga_schedule(
        jscjobid, jscname, jscdesc, jscenabled,
        jscstart, jscend, jscminutes, jschours, jscweekdays, jscmonthdays, jscmonths
    )
    VALUES (
        jid, 'everyminute', '', true,
        '2023-01-05 21:10:00+09:00'::timestamptz,
        '2023-01-07 21:10:00+09:00'::timestamptz,

        -- jscminutes (0~59)
        ARRAY[
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true
        ]::boolean[],

        -- jschours (0~23)
        ARRAY[
            true,true,true,true,true,true,true,true,true,true,
            true,true,true,true,true,true,true,true,true,true,
            true,true,true,true
        ]::boolean[],

        -- jscweekdays (0~6, 일~토)
        ARRAY[true,true,true,true,true,true,true]::boolean[],

        -- jscmonthdays (1~31)
        ARRAY[
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true,
            true, true, true, true, true, true, true, true, true, true,
            true
        ]::boolean[],

        -- jscmonths (1~12)
        ARRAY[
            true,true,true,true,true,true,true,true,true,true,
            true,true
        ]::boolean[]
    )
    RETURNING jscid INTO scid;
END;
$$;

DROP SCHEMA pgagent CASCADE;