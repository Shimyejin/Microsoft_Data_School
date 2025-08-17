import requests
import urllib.parse
import re
import csv
import time
import os
from collections import defaultdict
 
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)
 
def fetch_news(query, retries=3):
    encoded_query = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=100&sort=date"
 
    headers = {
        "X-Naver-Client-Id": '',
        "X-Naver-Client-Secret": ''
    }
 
    for attempt in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("items", [])
        print(f"[{query}] 시도 {attempt + 1} 실패 (코드: {response.status_code})")
        time.sleep(1)
    print(f"[{query}] 최대 재시도 횟수 초과")
    return []
 
# ✅ 부동산 관련 키워드
real_estate_keywords = ["부동산", "아파트", "전세", "매매", "집값", "재건축", "입주"]
 
# ✅ 자치구 단위로 뉴스 저장할 데이터 구조
gu_news = defaultdict(list)
 
# ✅ CSV에서 자치구와 법정동 추출
with open("법정동_리스트.csv", 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    next(reader)  # 헤더 건너뛰기
    dong_data = [(row[0].strip(), row[2].strip()) for row in reader if len(row) >= 3 and row[0].strip() and row[2].strip()]
 
# ✅ 출력 폴더 생성
output_dir = "news_by_gu"
os.makedirs(output_dir, exist_ok=True)
 
# ✅ 자치구 + 행정동 + 키워드로 뉴스 수집
for gu, dong in dong_data:
    for keyword in real_estate_keywords:
        query = f"{dong} {keyword}"
        print(f"\n🔍 키워드: {query}")
        items = fetch_news(query)
 
        if items:
            for item in items:
                gu_news[gu].append([
                    dong,
                    keyword,
                    clean_html(item.get("title", "")),
                    clean_html(item.get("description", "")),
                    item.get("pubDate", ""),
                    item.get("link", "")
                ])
        else:
            print(f"❌ 저장 실패: {query}")
 
# ✅ 자치구별로 CSV 저장
for gu, rows in gu_news.items():
    filename = f"{output_dir}/{gu}.csv"
    with open(filename, mode="w", newline='', encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["행정동", "검색키워드", "제목", "내용", "날짜", "링크"])
        writer.writerows(rows)
    print(f"✅ 저장 완료: {filename}")