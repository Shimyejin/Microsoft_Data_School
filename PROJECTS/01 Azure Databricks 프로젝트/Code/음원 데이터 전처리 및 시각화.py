# Databricks notebook source
# 노트북 다시 시작
dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ### 데이터 전처리

# COMMAND ----------

# MAGIC %md
# MAGIC **🔗 사이트:** [https://www.genie.co.kr/playlist/tags](https://www.genie.co.kr/playlist/tags)
# MAGIC
# MAGIC **🎼 장르**  
# MAGIC 가요, 발라드, 댄스, 락/메탈, POP, 랩/힙합, 일렉트로니카, 인디, 블루스/포크, 트롯, OST, JPOP, 재즈, 클래식, 뉴에이지, 월드뮤직
# MAGIC
# MAGIC **🏞 상황**
# MAGIC
# MAGIC 출/퇴근길, 휴식, 일/공부, 집, 외출, 카페, 휴가/여행, 드라이브, 산책, 잠잘 때, 운동, 하우스파티, 시상식, 집중, 거리, 클럽, 고백, 해변, 공연, 라운지, 애도
# MAGIC
# MAGIC **💭 감성**
# MAGIC
# MAGIC 기분전환, 외로움, 슬픔, 힘찬, 이별, 지침/힘듦, 설렘, 위로, 사랑, 스트레스/짜증, 그리움, 추억, 우울, 행복, 불만, 분노, 기쁨, 축하
# MAGIC
# MAGIC **🕰️ 시간대**  
# MAGIC 오후, 밤, 새벽, 저녁, 아침
# MAGIC
# MAGIC **🌈 스타일**
# MAGIC
# MAGIC 밝은, 신나는, 편안한, 따뜻한, 그루브한, 부드러운, 로맨틱한, 웅장한, 매혹적인, 영화음악, 잔잔한, 몽환적인, 댄서블한, 달콤한, 시원한, 애절한, 어두운, 연주음악, 캐롤, 발렌타인데이, 화이트데이, 섹시한, 로파이
# MAGIC
# MAGIC **🌤 날씨**
# MAGIC
# MAGIC 맑은날, 추운날, 흐린날, 비오는날, 더운날, 안개낀날, 눈오는날
# MAGIC
# MAGIC **🌸 계절**  
# MAGIC 봄, 여름, 가을, 겨울
# MAGIC

# COMMAND ----------

# 데이터 불러오기
import pandas as pd
import os

# 데이터 폴더 경로 설정
data_dir = "/Workspace/Users/1dt030@msacademy.msai.kr/Genie Data/"

# "연관태그포함"이 포함된 파일 목록 가져오기
file_list = [f for f in os.listdir(data_dir) if f.endswith(".csv") and "연관태그포함" in f]

# 각 파일을 데이터프레임으로 읽고 genre 정보를 추가
df_list = []
for file in file_list:
    genre_name = file.replace("genie_", "").replace("_음원_연관태그포함.csv", "")
    df = pd.read_csv(os.path.join(data_dir, file))
    df_list.append(df)

# 하나의 데이터프레임으로 합치기
genie_data = pd.concat(df_list, ignore_index=True)
genie_data = genie_data.rename(columns={"음원제목": "곡명"})
genie_data


# COMMAND ----------

# 태그 카테고리 정의
situation_tags = ['출/퇴근길', '휴식', '일/공부', '집', '외출', '카페', '휴가/여행', '드라이브', '산책', '잠잘 때', '운동', '하우스파티', '시상식', '집중', '거리', '클럽', '고백', '해변', '공연', '라운지', '애도']

emotion_tags = ['기분전환', '외로움', '슬픔', '힘찬', '이별', '지침/힘듦', '설렘', '위로', '사랑', '스트레스/짜증', '그리움', '추억', '우울', '행복', '불만', '분노', '기쁨', '축하']

time_tags = ['오후', '밤', '새벽', '저녁', '아침']

style_tags = ['밝은', '신나는', '편안한', '따뜻한', '그루브한', '부드러운', '로맨틱한', '웅장한', '매혹적인', '영화음악', '잔잔한', '몽환적인', '댄서블한', '달콤한', '시원한', '애절한', '어두운', '연주음악', '캐롤', '발렌타인데이', '화이트데이', '섹시한', '로파이']

season_tags = ['봄', '여름', '가을', '겨울']

weather_tags = ['맑은날', '추운날', '흐린날', '비오는날', '더운날', '안개낀날', '눈오는날']

# 연관태그에서 해당 리스트 추출 함수
def extract_tags_as_list(tag_string, tag_list):
    return [tag for tag in tag_list if tag in tag_string] if pd.notnull(tag_string) else []

# 카테고리별 태그 추출 적용
genie_data['상황태그'] = genie_data['연관태그'].apply(lambda x: extract_tags_as_list(x, situation_tags))
genie_data['감성태그'] = genie_data['연관태그'].apply(lambda x: extract_tags_as_list(x, emotion_tags))
genie_data['시간대태그'] = genie_data['연관태그'].apply(lambda x: extract_tags_as_list(x, time_tags))
genie_data['스타일태그'] = genie_data['연관태그'].apply(lambda x: extract_tags_as_list(x, style_tags))
genie_data['계절태그'] = genie_data['연관태그'].apply(lambda x: extract_tags_as_list(x, season_tags))
genie_data['날씨태그'] = genie_data['연관태그'].apply(lambda x: extract_tags_as_list(x, weather_tags))

# 결과 확인
display(genie_data)

# COMMAND ----------

# 태그가 모두 비어있는 경우 삭제
# 삭제 전 총 행 수
original_len = len(genie_data)

# 조건: 4개 태그 컬럼 모두 빈 리스트인 경우만 True
empty_tag_rows = genie_data[
    (genie_data['상황태그'].apply(len) == 0) &
    (genie_data['감성태그'].apply(len) == 0) &
    (genie_data['스타일태그'].apply(len) == 0) &
    (genie_data['계절태그'].apply(len) == 0) &
    (genie_data['시간대태그'].apply(len) == 0) &
    (genie_data['날씨태그'].apply(len) == 0)
]


# 삭제
genie_data = genie_data.drop(empty_tag_rows.index)

# 삭제 후 행 수
new_len = len(genie_data)

# 삭제된 행 수 출력
print(f"삭제된 행 수: {original_len - new_len}개")

# COMMAND ----------

# 연관태그 컬럼 삭제
genie_data = genie_data.drop(columns=['연관태그'])

display(genie_data)

# COMMAND ----------

# NaN 삭제
# 삭제 전 행 수 저장
before_len = len(genie_data)

# NaN 제거
genie_data = genie_data[genie_data['곡명'].notna() & genie_data['앨범'].notna()]

# 빈 문자열 제거 (공백만 있는 것도 포함)
genie_data = genie_data[
    (genie_data['곡명'].str.strip() != '') &
    (genie_data['앨범'].str.strip() != '')
]

# COMMAND ----------

genie_data.describe()

# COMMAND ----------

deduped_data.describe()

# COMMAND ----------

# 1. 곡명 + 가수 + 장르가 모두 같은 경우 → 중복 제거 (하나만 남김)
deduped_data = genie_data.drop_duplicates(subset=['곡명', '가수', '장르'])

# COMMAND ----------

# 카탈로그에 저장
# Pandas → Spark 변환
spark.sql("DROP TABLE IF EXISTS genie.genie_playlist")

spark_df = spark.createDataFrame(deduped_data)

# Genie 스키마 아래에 테이블 저장
spark_df.write.mode("overwrite").saveAsTable("genie.genie_playlist")

# COMMAND ----------

# CSV로 저장 (index 없이 저장)
# 1. UTF-8-SIG로 다시 저장 (엑셀 호환)
deduped_data.to_csv("genie_data.csv", index=False, encoding="utf-8-sig")

# COMMAND ----------

# Workspace 파일을 DBFS FileStore로 복사
dbutils.fs.cp(
    "file:/Workspace/Users/1dt030@msacademy.msai.kr/genie_data.csv", 
    "dbfs:/FileStore/genie/genie_data.csv"
)

# COMMAND ----------

# https://adb-4467770168345696.16.azuredatabricks.net/files/genie/genie_data.csv

# COMMAND ----------

# MAGIC %md
# MAGIC ### 시각화

# COMMAND ----------

# Spark SQL 방식
df = spark.sql("SELECT * FROM genie.genie_playlist")
display(df)

# COMMAND ----------

from pyspark.sql import functions as F

# 태그 컬럼 리스트
tag_columns = ["상황태그", "감성태그", "시간대태그", "스타일태그", "계절태그", "날씨태그"]

# 장르 컬럼명
genre_col = "장르"

# 태그별 존재 여부를 0/1로 변환
df_tags = df
for col in tag_columns:
    df_tags = df_tags.withColumn(
        f"{col}_exists", 
        F.when(F.size(F.col(col)) > 0, 1).otherwise(0)
    )

# explode 대신 melt 형태로 변환 (stack)
dfs = []
for col in tag_columns:
    dfs.append(
        df_tags.select(genre_col, F.lit(col).alias("tag_type"), F.col(f"{col}_exists").alias("tag_exists"))
    )

from functools import reduce
union_df = reduce(lambda a, b: a.union(b), dfs)

# 태그 존재하는 경우만 필터링 후 groupBy
tag_count = (
    union_df
    .filter(F.col("tag_exists") == 1)
    .groupBy(genre_col, "tag_type")
    .count()
    .orderBy(genre_col, "tag_type")
)

display(tag_count)

# COMMAND ----------

from pyspark.sql import functions as F

# 태그 컬럼 리스트
tag_columns = ["상황태그", "감성태그", "시간대태그", "스타일태그", "계절태그", "날씨태그"]

# 각 태그 컬럼별로 explode하고 count
for col in tag_columns:
    # explode_outer로 리스트 분리
    df_exploded = df.withColumn(col, F.explode_outer(col))
    
    # 태그별 곡 개수 집계
    tag_count = (
        df_exploded
        .groupBy(col)
        .count()
        .orderBy(F.desc("count"))
    )
    
    # 시각화 (Databricks 대시보드)
    display(tag_count)
