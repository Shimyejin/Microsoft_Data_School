import os
import re
import csv
import time
import requests
import urllib.parse
from email.utils import parsedate_to_datetime
from datetime import datetime

# =========================
# 설정
# =========================
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "z4l3gs4Pp86kkDapHlze")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "dT3dctr7PF")

OUTPUT_CSV = "today_news.csv"
SLEEP_SEC = 0.3

# =========================
# 유틸
# =========================
def clean_html(raw_html: str) -> str:
    return re.sub(re.compile("<.*?>"), "", raw_html or "")

def to_date_yyyy_mm_dd(pub_date: str) -> str:
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt.date().isoformat()
    except Exception:
        return pub_date or ""

def fetch_news_items(query: str, display: int = 100, sort: str = "date", retries: int = 3):
    encoded_query = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display={display}&sort={sort}"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    for attempt in range(retries):
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("items", [])
        time.sleep(1)
    return []

# =========================
# 메인
# =========================
def main():
    keyword = input("검색할 키워드를 입력하세요: ").strip()

    today_str = datetime.now().date().isoformat()  # YYYY-MM-DD
    rows = []

    items = fetch_news_items(keyword, display=100, sort="date")
    for it in items:
        content = clean_html(it.get("description", ""))
        date_ymd = to_date_yyyy_mm_dd(it.get("pubDate", ""))

        if date_ymd == today_str:  # 오늘 날짜만 필터링
            rows.append([keyword, content, date_ymd])

    # 저장
    os.makedirs(os.path.dirname(OUTPUT_CSV) or ".", exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["키워드", "뉴스 내용", "날짜"])
        w.writerows(rows)

    print(f"✅ 저장 완료: {OUTPUT_CSV} (오늘 기사 {len(rows)}건)")

if __name__ == "__main__":
    main()
