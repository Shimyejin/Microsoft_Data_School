-- env_cond 테이블에 대해 온도와 습도값이 기준 이상/이하인 경우 자동 감지 메시지 
-- 또는 로깅을 수행하는 트리거 만들기

-- 01. 로그 테이블 생성(이상 탐지 결과 기록용)
CREATE TABLE IF NOT EXISTS env_alert_log (
    id SERIAL PRIMARY KEY,
    farm CHAR(1),
    date DATE,
    alert TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 02. 트리거 함수 생성
CREATE OR REPLACE FUNCTION fn_insert_env_alert()
RETURNS TRIGGER AS $$
BEGIN
    -- 온도 이상
    IF NEW.temp > 25 THEN
        INSERT INTO env_alert_log(farm, date, alert, created_at)
        VALUES (NEW.farm, NEW.date, '온도 과다', NOW());
    END IF;

    -- 습도 이상
    IF NEW.humid > 60 THEN
        INSERT INTO env_alert_log(farm, date, alert, created_at)
        VALUES (NEW.farm, NEW.date, '습도 과다', NOW());
    ELSIF NEW.humid < 60 THEN
        INSERT INTO env_alert_log(farm, date, alert, created_at)
        VALUES (NEW.farm, NEW.date, '습도 부족', NOW());
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;



-- 03. 트리거 생성
CREATE TRIGGER trg_env_cond_alert
AFTER INSERT ON public.env_cond
FOR EACH ROW
EXECUTE FUNCTION fn_insert_env_alert();


-- 04. 테스트 예시
-- 온도 정상, 습도 과다
INSERT INTO env_cond (farm, date, temp, humid, light_hr, lux)
VALUES ('B', '2025-05-12', 25, 85, 14, 10);

-- 온도 정상, 습도 부족
INSERT INTO env_cond (farm, date, temp, humid, light_hr, lux)
VALUES ('B', '2025-05-13', 25, 40, 14, 10);


SELECT * FROM env_alert_log;


