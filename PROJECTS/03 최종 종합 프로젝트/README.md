# 💹 ITC: 암호화폐 시장 학습 시뮬레이션

> 실시간 및 과거 암호화폐 데이터를 활용하여 투자 전략을 학습하고,
> 개인 맞춤형 분석과 보고서를 제공하는 학습형 시뮬레이션 플랫폼입니다.

---

## 🔗 링크
[ITC 서비스 바로가기](https://itc.today/)

---
## 📌 프로젝트 개요

ITC(Investment Training & Consulting)는 암호화폐 실시간 시세 및 과거 데이터를 기반으로 **모의투자·시뮬레이션**을 제공하고,
사용자 거래 이력을 바탕으로 **맞춤형 보고서**와 **AI 챗봇 분석**을 지원하는 학습형 투자 시뮬레이션 서비스입니다.   
투자 경험이 부족한 사용자가 안전하게 전략을 실습하고 인사이트를 얻을 수 있도록 돕는 것을 목표로 합니다.

---

## ⚙ 사용 기술 및 도구

| 영역          | 도구 / 기술                              |
| ----------- | ------------------------------------ |
| 데이터 수집      | Upbit API, Azure Functions           |
| 데이터 저장      | MariaDB, Azure SQL Database          |
| 백엔드         | Node.js (Express, WebSocket)         |
| 데이터 분석      | Azure OpenAI, Hugging Face           |
| 시각화         | Chart.js Financial, Power BI, Fabric |
| 인증·보안       | Keycloak, Azure Key Vault            |
| DevOps & 배포 | Azure DevOps, AKS (Kubernetes)       |

---

## 🧠 주요 기능 및 로직

### 1. 실시간 모의투자

* Upbit API를 통해 BTC, ETH, XRP 등 주요 코인 실시간 시세·호가창 수집
* Node.js WebSocket 기반 매수·매도, 주문 체결 기능 구현
* 거래 동시성 제어: **트랜잭션 원자성 보장, FOR UPDATE 잠금, 커넥션 풀 적용**

### 2. 과거 데이터 시뮬레이션

* MariaDB에 저장된 과거 데이터 기반 상승·하락·횡보 시나리오 제공
* Chart.js Financial로 캔들차트, 거래량 등 시각화

### 3. 실시간 뉴스 수집·분석

* Azure Functions로 주기적 뉴스 크롤링 자동화
* 초기 Hugging Face 감성분석 → 성능 문제로 **Azure OpenAI 전환**, 한국어 기사 처리 품질 개선

### 4. 개인 맞춤형 분석 & RAG 챗봇

* 사용자 거래 이력 기반 PDF 보고서 생성 (손익, 총자산, 보유 종목 등)
* RAG 챗봇(Azure OpenAI)을 통한 투자 결과 해석 및 Q&A 지원

### 5. 인프라 및 운영

* Keycloak으로 사용자 인증 및 권한 관리
* Azure DevOps + AKS로 CI/CD 파이프라인 구축, 무중단 배포 실현
* Power BI + Fabric 대시보드로 기업 고객용 시각화 제공

---

## 📽 시연 흐름

1. 사용자가 모의투자 시작 (실시간 / 과거 시나리오 선택)
2. Upbit API 실시간 데이터 수집 → MariaDB 저장
3. Azure Functions → 뉴스 자동 수집
4. Azure OpenAI → 뉴스 감성분석 및 챗봇 분석
5. 개인 맞춤형 보고서 생성 + Power BI 대시보드 시각화 제공

---

## 💡 프로젝트 차별점

* **실시간 + 과거 시뮬레이션 통합** → 실제 투자와 유명
