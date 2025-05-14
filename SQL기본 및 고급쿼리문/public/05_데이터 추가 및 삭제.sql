-- 1-1. 데이터 한 건 추가하기
INSERT INTO master_code(
column_nm, type, code, code_desc)
VALUES ('breeds', 'txt', 'R1', 'Ross');

SELECT * FROM master_code WHERE column_nm = 'breeds';

-- 1-2. 데이터 여러 건 추가하기
INSERT INTO master_code(
column_nm, type, code, code_desc)
VALUES
('breeds', 'txt', 'N1', 'New Hampshire Red'),
('breeds', 'txt', 'R2', 'Rhode Island Red'),
('breeds', 'txt', 'A1', 'Australorp');

-- 2-1. 데이터 수정하기
UPDATE master_code
SET code_desc='암컷'
WHERE column_nm = 'gender' AND code = 'F';

SELECT * FROM master_code WHERE column_nm = 'gender';

-- 3-1. 모든 데이터 삭제하기
DELETE FROM master_code;
ROLLBACK;

-- 3-2. 특정 조건의 데이터 삭제하기
DELETE FROM master_code
WHERE column_nm = 'size_stand' AND TO_NUMBER(code, '99') < 10;