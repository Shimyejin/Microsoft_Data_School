import os
import time
import pandas as pd
from openai import AzureOpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from glob import glob

# 🔐 환경 변수 로딩
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ✅ 감정 분석 함수 (429 에러 시 최대 3회 재시도 + 1초 대기)
def get_sentiment_score(text):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 뉴스 요약 정서를 평가하는 중립적인 분석 도우미입니다. 사용자가 제공한 뉴스 제목과 내용을 읽고, 전반적인 정서를 1~5 사이의 정수로 평가해 주세요. 숫자만 출력하세요. (1은 매우 부정적, 5는 매우 긍정적)"
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.2,
                max_tokens=5
            )
            score = int(response.choices[0].message.content.strip())
            return score
        except Exception as e:
            err_msg = str(e)
            print(f"[오류] 감정 분석 실패: {err_msg}")
            if "429" in err_msg:
                time.sleep(1)
                continue
            break
    return None

# ✅ 자치구별 뉴스 파일 폴더 경로
folder_path = r"C:\Users\EL47\Documents\VSCode\Data School\project2\네이버뉴스_부동산"
csv_files = glob(os.path.join(folder_path, "*.csv"))

# ✅ 결과 저장 파일 경로
output_path = os.path.join("C:/Users/EL47/Documents/VSCode/Data School/project2", "부동산_감정분석_결과.csv")

# ✅ 이미 처리한 결과 불러오기 (중단 대비용)
if os.path.exists(output_path):
    processed = pd.read_csv(output_path)
    done_set = set(zip(processed["자치구"], processed["법정동"], processed["검색키워드"]))
else:
    # 없으면 새로 생성
    pd.DataFrame(columns=["자치구", "법정동", "검색키워드", "평균감정점수"]).to_csv(output_path, index=False, encoding="utf-8-sig")
    done_set = set()

# ✅ 각 자치구별 뉴스 파일 처리
for file in tqdm(csv_files):
    district = os.path.basename(file).replace(".csv", "")
    df = pd.read_csv(file)

    # 필요한 컬럼만 추출 후 결측치 제거
    df = df[["법정동", "검색키워드", "제목", "내용"]].dropna()

    grouped = df.groupby(["법정동", "검색키워드"])

    for (dong, keyword), group in grouped:
        if (district, dong, keyword) in done_set:
            continue  # ✅ 이미 처리된 항목은 건너뜀

        scores = []
        for _, row in group.iterrows():
            combined_text = f"{row['제목']} {row['내용']}"
            score = get_sentiment_score(combined_text)
            if score:
                scores.append(score)

        if scores:
            avg_score = round(sum(scores) / len(scores), 2)
            result_row = pd.DataFrame([{
                "자치구": district,
                "법정동": dong,
                "검색키워드": keyword,
                "평균감정점수": avg_score
            }])
            result_row.to_csv(output_path, mode='a', header=False, index=False, encoding="utf-8-sig")
