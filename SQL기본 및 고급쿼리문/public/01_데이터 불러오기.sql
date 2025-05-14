-- 1. 병아리 기본 정보
CREATE TABLE chick_info (
    chick_no CHAR(8) PRIMARY KEY,
    breeds CHAR(2) NOT NULL,
    gender CHAR(1) NOT NULL,
    hatchday DATE NOT NULL,
    egg_weight SMALLINT NOT NULL,
    vaccination1 SMALLINT,
    vaccination2 SMALLINT,
    farm CHAR(1) NOT NULL
);

-- 2. 환경 정보
CREATE TABLE env_cond (
    farm CHAR(1) NOT NULL,
    date DATE NOT NULL,
    temp SMALLINT NOT NULL,
    humid FLOAT,
    light_hr FLOAT,
    lux FLOAT
);

-- 3. 건강 상태
CREATE TABLE health_cond (
    chick_no CHAR(8) NOT NULL,
    check_date DATE NOT NULL,
    weight SMALLINT NOT NULL,
    body_temp NUMERIC(3,1) NOT NULL,
    breath_rate SMALLINT NOT NULL,
    feed_intake SMALLINT NOT NULL,
    diarrhea_yn CHAR(1) NOT NULL,
    note VARCHAR(255),
    FOREIGN KEY (chick_no) REFERENCES chick_info(chick_no)
);
UPDATE health_cond
SET note = '체온이 45도를 넘어가고, 호흡수가 빠르며 사료 섭취량이 20% 가량 줄었음'
WHERE chick_no = 'B2310019' AND check_date = '2023-01-30';


-- 4. 코드 관리
CREATE TABLE master_code (
  column_nm VARCHAR(12) NOT NULL,
  type VARCHAR(6) NOT NULL,
  code VARCHAR(2) NOT NULL,
  code_desc VARCHAR(30) NOT NULL
);

INSERT INTO master_code (column_nm, type, code, code_desc)
VALUES
  ('breeds', 'txt', 'C1', 'Cornish'),
  ('breeds', 'txt', 'C2', 'Plymouth'),
  ('breeds', 'txt', 'B1', 'Leghorn'),
  ('breeds', 'txt', 'D1', 'Orpington'),
  ('gender', 'txt', 'M', '수컷'),
  ('gender', 'txt', 'F', '암컷'),
  ('vaccination1', 'binary', '0', '미접종'),
  ('vaccination1', 'binary', '1', '접종'),
  ('vaccination2', 'binary', '0', '미접종'),
  ('vaccination2', 'binary', '1', '접종'),
  ('disease_yn', 'binary', 'Y', '질병'),
  ('disease_yn', 'binary', 'N', '정상'),
  ('pass_fail', 'binary', 'P', '합격'),
  ('pass_fail', 'binary', 'F', '불합격'),
  ('size_stand', 'number', '7', '7호'),
  ('size_stand', 'number', '8', '8호'),
  ('size_stand', 'number', '9', '9호'),
  ('size_stand', 'number', '10', '10호'),
  ('size_stand', 'number', '11', '11호');


-- 5. 생산 실적
CREATE TABLE prod_result (
    chick_no CHAR(8) NOT NULL,
    prod_date DATE NOT NULL,
    raw_weight SMALLINT NOT NULL,
    disease_yn CHAR(1) NOT NULL,
    size_stand SMALLINT NOT NULL,
    pass_fail CHAR(1) NOT NULL,
    FOREIGN KEY (chick_no) REFERENCES chick_info(chick_no)
);

-- 6. 출하 정보
CREATE TABLE ship_result (
    chick_no CHAR(8) NOT NULL,
    order_no CHAR(4) NOT NULL,
    customer VARCHAR(7) NOT NULL,
    due_date DATE NOT NULL,
    arrival_date DATE NOT NULL,
    destination VARCHAR(2) NOT NULL,
    FOREIGN KEY (chick_no) REFERENCES chick_info(chick_no)
);

INSERT INTO ship_result (chick_no, order_no, customer, due_date, arrival_date, destination)
VALUES
  ('A2310001', 'B001', 'BBQUEEN', '2023-02-05', '2023-02-05', '부산'),
  ('A2310002', 'M002', 'MAXCANA', '2023-02-05', '2023-02-04', '당진'),
  ('A2310003', 'M002', 'MAXCANA', '2023-02-05', '2023-02-04', '당진'),
  ('A2300004', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('A2300005', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('A2310006', 'B002', 'BBQUEEN', '2023-02-05', '2023-02-05', '울산'),
  ('A2310007', 'B002', 'BBQUEEN', '2023-02-05', '2023-02-05', '울산'),
  ('A2310008', 'M002', 'MAXCANA', '2023-02-05', '2023-02-04', '당진'),
  ('A2300009', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('A2300010', 'B001', 'BBQUEEN', '2023-02-05', '2023-02-05', '부산'),
  ('A2310011', 'B002', 'BBQUEEN', '2023-02-05', '2023-02-05', '울산'),
  ('A2310012', 'B002', 'BBQUEEN', '2023-02-05', '2023-02-05', '울산'),
  ('A2300013', 'B002', 'BBQUEEN', '2023-02-05', '2023-02-05', '울산'),
  ('A2300014', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('A2310015', 'M002', 'MAXCANA', '2023-02-05', '2023-02-04', '당진'),
  ('A2310016', 'M002', 'MAXCANA', '2023-02-05', '2023-02-04', '당진'),
  ('A2300017', 'B001', 'BBQUEEN', '2023-02-05', '2023-02-05', '부산'),
  ('A2300018', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('A2300019', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('A2300020', 'M001', 'MAXCANA', '2023-02-05', '2023-02-05', '대전'),
  ('B2310001', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2310002', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2310003', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2300004', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2300005', 'G001', 'GUBNA', '2023-02-05', '2023-02-05', '대구'),
  ('B2310006', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2300007', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2300008', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2300010', 'G001', 'GUBNA', '2023-02-05', '2023-02-05', '대구'),
  ('B2300011', 'G001', 'GUBNA', '2023-02-05', '2023-02-05', '대구'),
  ('B2300012', 'G001', 'GUBNA', '2023-02-05', '2023-02-05', '대구'),
  ('B2310013', 'G002', 'GUBNA', '2023-02-05', '2023-02-05', '광주'),
  ('B2300014', 'G002', 'GUBNA', '2023-02-05', '2023-02-05', '광주'),
  ('B2310015', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2310016', 'G001', 'GUBNA', '2023-02-05', '2023-02-05', '대구'),
  ('B2310017', 'G002', 'GUBNA', '2023-02-05', '2023-02-05', '광주'),
  ('B2310018', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울'),
  ('B2300020', 'Y001', 'YESYES', '2023-02-04', '2023-02-04', '서울');

-- 7. 단위 관리
CREATE TABLE unit (
    column_nm VARCHAR(11) PRIMARY KEY,
    unit VARCHAR(7) NOT NULL
);

INSERT INTO unit (column_nm, unit)
VALUES
  ('egg_weight', 'g'),
  ('weight', 'g'),
  ('body_temp', '℃'),
  ('breath_rate', 'cnt/min'),
  ('feed_intake', 'g/day'),
  ('temp', '℃'),
  ('humid', '%'),
  ('light_hr', 'hr/day'),
  ('lux', 'lx');