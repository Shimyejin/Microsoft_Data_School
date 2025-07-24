# 필요한 라이브러리 임포트
import azure.functions as func  # Azure Functions 기능을 사용하기 위한 라이브러리
import logging  # 로깅(실행 정보, 오류 등을 기록)을 위한 라이브러리
from openai import AzureOpenAI  # Azure OpenAI 서비스를 사용하기 위한 클라이언트
import json  # JSON 데이터를 처리하기 위한 라이브러리
import os  # 환경 변수 접근 등 운영체제 기능을 사용하기 위한 라이브러리
from azure.cosmos import CosmosClient  # Azure Cosmos DB 연결을 위한 클라이언트
from azure.cosmos.exceptions import CosmosHttpResponseError  # Cosmos DB 예외 처리
import time  # 시간 지연, 대기 등의 기능을 위한 라이브러리

# 상수 정의
APPLICATION_JSON = "application/json" # HTTP 응답 형식 지정을 위한 상수

# 환경 변수에서 설정 값 로드
# Azure OpenAI 설정
openai_endpoint = os.environ["OPENAI_ENDPOINT"]  # OpenAI API 엔드포인트 URL
openai_key = os.environ["OPENAI_KEY"]  # OpenAI API 인증 키
openai_api_version = os.environ["OPENAI_API_VERSION"]  # OpenAI API 버전
openai_gpt_model = os.environ["OPENAI_GPT_MODEL"]  # 사용할 GPT 모델 이름
openai_embeddings_deployment = os.environ["OPENAI_EMBEDDINGS_DEPLOYMENT"]  # 임베딩 모델 이름
# Azure Cosmos DB 설정
cosmos_endpoint = os.environ["COSMOSDB_ENDPOINT"]  # Cosmos DB 엔드포인트
cosmos_key = os.environ["COSMOSDB_KEY"]  # Cosmos DB 접근 키
cosmosdb_database = os.environ["COSMOSDB_DATABASE"]  # 사용할 데이터베이스 이름
cosmosdb_container = os.environ["COSMOSDB_CONTAINER"]  # 사용할 컨테이너 이름

# OpenAI 클라이언트 초기화 - AI 모델을 호출하기 위한 인터페이스
openai_client = AzureOpenAI(
    azure_endpoint=openai_endpoint,
    api_key=openai_key,
    api_version=openai_api_version
)

# Cosmos DB 클라이언트 초기화 - 데이터베이스 연결 설정
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database = cosmos_client.get_database_client(cosmosdb_database)
container = database.get_container_client(cosmosdb_container)

# 헬퍼 함수 정의
def solar_data_to_text(item):
    """ 태양광 데이터를 자연어 텍스트로 변환하는 함수
        매개변수:
            item (dict): 태양광 발전 데이터가 담긴 딕셔너리
        반환값:
            str: 데이터를 설명하는 자연어 텍스트
    """

        # 소수점 자릿수 제한
    pcap = round(float(item['pcap']), 2)
    qgen = round(float(item['qgen']), 2)
    usage_rate = round((qgen / pcap * 100), 2) if pcap > 0 else 0
    
    text = f"【위치】{item['city']} {item['county']} (위도 {round(float(item['lat']), 2)}, 경도 {round(float(item['lon']), 2)})\n"
    text += f"【날짜/시간】{item['fcstDate']} {item['fcstTime']}시\n"
    text += f"【발전 정보】설비용량: {pcap}kW | 발전량: {qgen}kW | 이용률: {usage_rate}%\n"
    text += f"【환경 조건】일사량: {item['srad']}W/㎡ | 온도: {item['temp']}°C | 풍속: {item['wspd']}m/s\n"
    
    # RAG 최적화를 위한 예상 질문 추가
    text += f"\nQ: {item['city']} {item['county']}의 {item['fcstDate'][:4]}년 {item['fcstDate'][5:7]}월 {item['fcstDate'][8:10]}일 {item['fcstTime'][:2]}시 태양광 발전량은?\n"
    text += f"A: 설비용량 {pcap}kW에서 {qgen}kW 발전하여 이용률은 {usage_rate}%입니다. 당시 일사량은 {item['srad']}W/㎡입니다."
    
    return text

def batch_generate_embeddings(texts, batch_size=20):
    """ 텍스트 배열에 대해 배치 단위로 임베딩(벡터화)을 생성하는 함수
    
        매개변수:
            texts (list): 임베딩할 텍스트 목록
            batch_size (int): 한 번에 처리할 텍스트 수(기본값: 20)

        반환값:
            list: 생성된 임베딩 벡터 목록
    """
    all_embeddings = []
    # 배치 크기만큼 나누어 처리
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            # OpenAI API를 호출하여 임베딩 생성
            response = openai_client.embeddings.create(
                input=batch,
                model=openai_embeddings_deployment
            )
            embeddings_data = response.model_dump()
            batch_embeddings = [data['embedding'] for data in embeddings_data['data']]
            all_embeddings.extend(batch_embeddings)
            logging.info(f"임베딩 배치 처리 완료: {i} ~ {i + len(batch)} / {len(texts)}")
        except Exception as e:
            logging.error(f"임베딩 생성 오류 (배치 {i}-{i+len(batch)}): {str(e)}")
             # 오류 발생 시 빈 임베딩으로 채우기 (1536은 일반적인 OpenAI 임베딩 차원)
            all_embeddings.extend([[0] * 1536] * len(batch))
    return all_embeddings

def prepare_items_for_cosmos(items):
    """ 데이터 항목을 Cosmos DB에 저장하기 위해 준비하는 함수
    
        매개변수:
        items (list): 처리할 데이터 항목 목록

        반환값:
            list: 임베딩과 ID가 추가된 데이터 항목 목록
    """
    # 각 항목에 대해 텍스트 표현 생성
    for item in items:
        item['locationText'] = f"{item['city']} {item['county']}"
        item['textRepresentation'] = solar_data_to_text(item)
        # 고유 ID 생성 (날짜_시간_지역코드 형식)
        item['id'] = f"{item['fcstDate']}_{item['fcstTime']}_{item['regCd']}"
    
    # 모든 텍스트 표현을 리스트로 추출
    locations = [item['locationText'] for item in items]
    texts = [item['textRepresentation'] for item in items]
    
    # 배치로 임베딩 생성
    location_embeddings = batch_generate_embeddings(locations)
    embeddings = batch_generate_embeddings(texts)
    
    for i, location_embedding in enumerate(location_embeddings):
        items[i]['locationVector'] = location_embedding

    # 생성된 임베딩을 각 항목에 추가
    for i, embedding in enumerate(embeddings):
        items[i]['contentVector'] = embedding
    
    return items

def bulk_insert_to_cosmos(items, batch_size=100, max_retries=5):
    """ 여러 항목을 Cosmos DB에 일괄 삽입하는 함수
    
        매개변수:
            items (list): 삽입할 데이터 항목 목록
            batch_size (int): 한 번에 처리할 항목 수(기본값: 100)
            max_retries (int): 실패 시 최대 재시도 횟수(기본값: 5)

        반환값:
            tuple: (성공한 항목 목록, 실패한 항목 목록)
    """
    successful_items = []  # 성공적으로 삽입된 항목 저장
    failed_items = []      # 삽입 실패한 항목 저장
    
    # 배치 크기로 항목들 나누기
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    for batch_index, batch in enumerate(batches):
        retry_count = 0
        # 최대 재시도 횟수까지 시도
        while retry_count < max_retries:
            try:
                batch_successful = []
                batch_failed = []
                
                # 배치 내 각 항목 처리
                for item in batch:
                    try:
                        # Cosmos DB에 항목 삽입 또는 업데이트
                        container.upsert_item(body=item)
                        batch_successful.append(item)
                    except CosmosHttpResponseError as e:
                        if e.status_code == 429:  # Too Many Requests (요청 제한)
                            # 요청 제한 발생 시 전체 배치 재시도
                            logging.warning(f"Cosmos DB 요청 제한 발생, 재시도 대기 중... (배치 {batch_index})")
                            retry_delay = int(e.http_headers.get('x-ms-retry-after-ms', 1000)) / 1000
                            time.sleep(retry_delay)
                            raise e  # 예외를 다시 발생시켜 예부 예외 처리로 배치 재시도
                        else:
                            # 다른 오류는 개별 항목만 실패로 처리
                            logging.error(f"아이템 삽입 오류 (ID: {item.get('id')}): {str(e)}")
                            batch_failed.append(item)
                
                # 성공 및 실패 항목을 결과 목록에 추가
                successful_items.extend(batch_successful)
                failed_items.extend(batch_failed)
                
                # 배치 처리 결과 로깅
                logging.info(f"배치 {batch_index+1}/{len(batches)} 처리 완료: {len(batch_successful)} 성공, {len(batch_failed)} 실패")
                
                # 현재 배치 처리 완료, 다음 배치로 이동
                break
                
            except CosmosHttpResponseError as e:
                # 전체 배치에 대한 오류 (주로 요청 제한)
                retry_count += 1
                # 지수 백오프: 재시도 간격을 점점 늘림 (최대 60초)
                retry_delay = min(2 ** retry_count, 60) 
                logging.warning(f"배치 {batch_index+1} 실패, {retry_count}/{max_retries} 재시도 (대기: {retry_delay}초): {str(e)}")
                time.sleep(retry_delay)
            
            except Exception as e:
                # 예상치 못한 기타 오류
                logging.error(f"배치 {batch_index+1} 처리 중 예상치 못한 오류: {str(e)}")
                failed_items.extend(batch)
                break
                
        # 최대 재시도 횟수 초과 시 실패로 처리
        if retry_count >= max_retries:
            logging.error(f"배치 {batch_index+1} 최대 재시도 횟수 초과, {len(batch)} 항목 실패")
            failed_items.extend(batch)
    
    return successful_items, failed_items

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="solar_predict_cosmosdb")
def solar_predict_cosmosdb(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # 요청 본문(JSON)을 파싱
        req_body = req.get_json()
        
        # 입력이 배열인 경우(여러 레코드) 또는 단일 레코드인 경우 모두 처리
        items = req_body if isinstance(req_body, list) else [req_body]

        # 데이터 준비 (텍스트 변환 및 임베딩 생성)
        prepared_items = prepare_items_for_cosmos(items)

        # Cosmos DB에 일괄 삽입
        successful_items, failed_items = bulk_insert_to_cosmos(
            prepared_items,
            batch_size=25,
            max_retries=3
        )

        # 처리 결과 생성
        result = {
            "status": "완료" if not failed_items else "부분 완료",
            "total_requested": items,
            "total_processed": len(prepared_items),
            "successful": len(successful_items),
            "failed": len(failed_items)
        }

        # HTTP 200 응답 반환
        return func.HttpResponse(
            json.dumps(result),
            mimetype=APPLICATION_JSON,
            status_code=200
        )
    except Exception as e:
        # 오류 발생 시 HTTP 500 오류 응답 반환
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            mimetype="application/json",
            status_code=500
        )
    
def query_similar_data(user_query, top_k=5):
    """ 사용자 질의와 의미적으로 유사한 태양광 데이터를 검색하는 함수
    
        매개변수:
            user_query (str): 사용자 질의 텍스트
            top_k (int): 반환할 최대 유사 데이터 수(기본값: 5)

        반환값:
            list: 유사한 데이터 목록
    """
    # 사용자 질의를 벡터(임베딩)로 변환
    embedding_response = openai_client.embeddings.create(
        input=user_query,
        model=openai_embeddings_deployment
    )
    query_vector = embedding_response.data[0].embedding
    
    # Cosmos DB에서 벡터 유사도 검색 쿼리 실행
    # VectorDistance 함수로 벡터 간 거리(유사도)를 계산하여 정렬
    query = f"""
    SELECT TOP {top_k} c.textRepresentation, c.city, c.county, c.fcstDate, 
           c.fcstTime, c.pcap, c.qgen, c.srad, c.temp, c.wspd
    FROM c 
    ORDER BY VectorDistance(c.contentVector, {query_vector})
    """

    # 쿼리 실행 및 결과 반환
    results = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    return results

def generate_response(user_query):
    """ RAG(Retrieval-Augmented Generation) 패턴으로 사용자 질의에 대한 응답 생성
    
        매개변수:
            user_query (str): 사용자 질의 텍스트

        반환값:
            str: 생성된 응답 텍스트
    """
    # 1. 관련 데이터 검색 (Retrieval 단계)
    context_data = query_similar_data(user_query)
    
    # 2. 검색된 데이터로 컨텍스트 구성
    context = "다음은 질문과 관련된 태양광 발전 데이터입니다:\n\n"
    for i, data in enumerate(context_data, 1):
        context += f"데이터 {i}: {data['textRepresentation']}\n\n"
    
    # 3. OpenAI 모델을 사용하여 응답 생성 (Generation 단계)
    messages = [
        {"role": "system", "content": "당신은 태양광 발전 데이터 분석 전문가입니다. 제공된 데이터를 바탕으로 정확하고 유익한 정보를 제공해주세요."},
        {"role": "user", "content": f"질문: {user_query}\n\n컨텍스트: {context}"}
    ]
    
    # 채팅 완성 API 호출
    response = openai_client.chat.completions.create(
        model= openai_gpt_model,
        messages=messages,
        temperature=0.3 # 낮은 temperature로 보다 일관된 응답 생성
    )
    
    return response.choices[0].message.content

@app.route(route="chat_rag", methods=[func.HttpMethod.POST])
def chat_rag(req: func.HttpRequest) -> func.HttpResponse:
    """ RAG 기반 질의응답 처리를 위한 HTTP 엔드포인트
    
        매개변수:
            req (HttpRequest): HTTP 요청 객체

        반환값:
            HttpResponse: HTTP 응답 객체
    """
    logging.info('Python HTTP trigger function processed a request.')

    # 요청에서 사용자 질문 추출
    req.get_json()
    user_question = req.get_json().get("question")
    logging.info(user_question)
    # RAG 방식으로 응답 생성
    answer = generate_response(user_question)
    logging.info(answer)

    # 응답 반환
    return func.HttpResponse(
        json.dumps({"status": "success", "items": answer}),
        mimetype=APPLICATION_JSON,
        status_code=200
    )