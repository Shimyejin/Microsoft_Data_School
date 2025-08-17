import pandas as pd
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from collections import Counter

# ✅ 1. 환경변수 로딩 (.env 파일 필요)
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ✅ 2. Azure OpenAI 요약 함수
def generate_summary(texts, district, dong):
    combined_text = "\n\n".join(texts)
    prompt = f"""
너는 부동산 전문가야. 아래는 서울특별시 {district} {dong}에 위치한 아파트 및 오피스텔들의 주민 리뷰 요약이야.
이 텍스트들을 바탕으로 {dong}이라는 동네에 대한 전반적인 분위기, 생활환경, 장단점을 종합해서 설명해줘.
문장은 3~5줄 정도의 단락 하나로 자연스럽게 작성해줘. 키워드 나열은 하지 마.

{combined_text}
    """
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "당신은 동네 평가를 전문적으로 요약하는 부동산 어시스턴트입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# ✅ 3. CSV 불러오기
df = pd.read_csv("서울시_호갱노노.csv")
df["자치구"] = df["주소"].str.extract(r'서울특별시\s(.*?)\s')
df["요약글"] = df["요약글"].fillna("")
df["해시태그"] = df["해시태그"].fillna("")

# ✅ 4. 해시태그 전체 빈도 계산
all_tags = [tag.strip() for tags in df["해시태그"] for tag in tags.split(",") if tag.strip()]
tag_counter = Counter(all_tags)

# ✅ 5. 그룹별 처리 함수 (진행 상황 출력 추가)
def process_group(group):
    district = group["자치구"].iloc[0]
    dong = group["법정동"].iloc[0]

    print(f"🔄 요약 중: {district} {dong}...")  # ✅ 진행상황 출력
    
    summary = generate_summary(group["요약글"].tolist(), district, dong)
    
    apt_names = sorted(set(name.replace(dong + " ", "") for name in group["단지명"]))
    
    tags = [tag.strip() for tags in group["해시태그"] for tag in tags.split(",") if tag.strip()]
    unique_tags = sorted(set(tags), key=lambda x: -tag_counter[x])
    
    print(f"✅ 완료: {district} {dong}")  # ✅ 완료 표시

    return pd.Series({
        "요약글": summary,
        "해시태그": ", ".join(unique_tags),
        "리스트": ", ".join(apt_names)
    })

# ✅ 6. 전체 적용
final_df = df.groupby(["자치구", "법정동"], group_keys=False).apply(process_group).reset_index()

# ✅ 7. 저장
final_df.to_csv("행정동_요약_최종.csv", index=False)
print("📁 전체 저장 완료: 행정동_요약_최종.csv")