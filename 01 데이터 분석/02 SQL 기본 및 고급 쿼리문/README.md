# SQL기본 및 고급쿼리문

Microsoft Data School 1기에서 수행한 PostgreSQL 기반 SQL 실습과 이를 바탕으로 구현한 Flask 웹 프로젝트를 정리한 공간입니다.

## 📌 1. PostgreSQL 실습 개요

### ✅ 주요 SQL 실습 내용

| 주제 | 설명 |
|------|------|
| **데이터베이스 생성 및 테이블 정의** | `CREATE DATABASE`, `CREATE TABLE`, 제약조건 설정 |
| **CRUD** | `INSERT`, `SELECT`, `UPDATE`, `DELETE` 실습 |
| **필터링 및 정렬** | `WHERE`, `ORDER BY`, `LIMIT`, `LIKE` |
| **JOIN 문법** | `INNER JOIN`, `LEFT JOIN`, 서브쿼리로 다중 테이블 연결 |
| **집계 및 그룹화** | `GROUP BY`, `HAVING`, `COUNT`, `SUM`, `AVG` 등 |
| **서브쿼리 및 뷰 생성** | 복잡한 쿼리 분리 및 재사용 |
| **인덱스 및 성능 튜닝** | `EXPLAIN`, `CREATE INDEX` 실습 |

---

## 🚀 2. Flask 웹 애플리케이션 개발

PostgreSQL에 저장된 데이터를 기반으로 **웹 페이지**를 Flask로 구현했습니다.

### 🔧 사용 스택
- **Back-end**: Python Flask
- **Database**: PostgreSQL
- **Front-end**: HTML + TailwindCSS + Jinja2
- **환경관리**: dotenv (`.env`)로 DB 설정 분리

### 🧩 주요 기능

| 기능 | 설명 |
|------|------|
| **상품 필터링/검색** | 무신사 상품 목록 필터링 (카테고리, 가격, 할인 등) |
| **좋아요 및 위시리스트** | 상품 찜 기능 (하트) |
| **위시리스트 CRUD** | 위시리스트 수정, 삭제, 메모 기능 |
| **데이터 시각화** | 브랜드별 할인율, 할인율별 평균 리뷰수 등 시각화 (Charts 탭) |
| **Dashboard 구성** | 여러 지표를 하나의 대시보드에 시각화

