import ast
import base64
from collections import defaultdict
import json
import logging
import os
import pickle
import ssl
import time
import traceback
import uuid
from datetime import datetime
from io import BytesIO
from threading import Lock
import requests
import pytubefix.request
import yt_dlp
from PIL import Image
from pytube import YouTube
from werkzeug.utils import secure_filename
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import concurrent.futures
from PIL import Image, ExifTags

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 기본 환경 설정
PICKLE_FILENAME = "temp_result.pkl"

# 로컬 업로드 폴더 설정
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 보안 및 인증 관련 설정
ssl._create_default_https_context = ssl._create_unverified_context

# Youtube API 설정
youtubeAPI_1 = "유튜브 API"
youtubeAPI_2 = "유튜브 API"
youtubeAPI_3 = "유튜브 API"
youtubeAPI_4 = "유튜브 API"
youtubeAPI_5 = "유튜브 API"
youtubeAPI_6 = "유튜브 API"
youtubeAPI_7 = "유튜브 API"
YOUTUBE_API_KEY = youtubeAPI_4

YOUTUBE_CREDENTIALS_PATH = 'credentials.json'
YOUTUBE_CLIENT_SECRETS_PATH = 'client_secrets.json'
youtube_service = None
youtube_lock = Lock()

# Databricks 설정
DATABRICKS_HOST = "DATABRICKS_HOST"
DATABRICKS_TOKEN = "DATABRICKS_TOKEN"
DATABRICKS_JOB_ID = DATABRICKS_JOB_ID

# 허용 이미지 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

# 장르 목록
genres = ["가요", "발라드", "댄스", "락/메탈", "POP", "랩/힙합", "일렉트로니카", "인디",
    "블루스/포크", "트롯", "OST", "JPOP", "재즈", "클래식", "뉴에이지", "월드뮤직"]

# Flask 초기화
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 환경 변수(.env 파일) 로드 
load_dotenv()

# 데이터베이스 연결 함수
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host = os.getenv('DB_HOST'),
            port = os.getenv('DB_PORT'),
            dbname = os.getenv('DB_NAME'),
            user = os.getenv('DB_USER'),
            password = os.getenv('DB_PASSWORD'),
            options = '-c timezone=Asia/Seoul')
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return None

def insert_image_data(web_file_path):  # ✅ 웹 경로만 받음
    """이미지 정보를 데이터베이스에 삽입하고 ID 반환"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO images (file_name, upload_time)
                VALUES (%s, %s)
                RETURNING id
            """, (web_file_path, datetime.now()))  # ✅ 웹 경로 저장
            
            image_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"이미지 데이터 삽입 완료: ID={image_id}")
            return image_id
            
    except Exception as e:
        conn.rollback()
        logger.error(f"이미지 데이터 삽입 실패: {e}")
        raise
    finally:
        conn.close()
        
def extract_single_tag_value(tag_value):
    """태그 값에서 첫 번째 값만 추출 (이미지는 단일 태그)"""
    if not tag_value:
        return ''
    
    if isinstance(tag_value, list):
        return tag_value[0] if tag_value else ''
    
    if isinstance(tag_value, str):
        try:
            # "['드라이브', '거리']" 형태면 첫 번째 값만 추출
            parsed = ast.literal_eval(tag_value)
            if isinstance(parsed, list):
                return parsed[0] if parsed else ''
            else:
                return str(parsed)
        except:
            # 파싱 실패시 원본 문자열 반환
            return tag_value.strip()
    
    return str(tag_value)

def insert_image_tags(image_id, tags_data):
    """이미지 태그를 데이터베이스에 삽입 (단일 TEXT 값으로)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO image_tags (image_id, tag_situation, tag_emotion, tag_time, tag_style, tag_weather, tag_season)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                image_id,
                extract_single_tag_value(tags_data.get('상황', '')),
                extract_single_tag_value(tags_data.get('감성', '')),
                extract_single_tag_value(tags_data.get('시간대', '')),
                extract_single_tag_value(tags_data.get('스타일', '')),
                extract_single_tag_value(tags_data.get('날씨', '')),
                extract_single_tag_value(tags_data.get('계절', ''))
            ))
            
            conn.commit()
            logger.info(f"이미지 태그 삽입 완료: image_id={image_id}")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"이미지 태그 삽입 실패: {e}")
        raise
    finally:
        conn.close()

def parse_tag_array(tag_value):
    """태그 문자열을 배열로 파싱"""
    if not tag_value:
        return []
    
    if isinstance(tag_value, list):
        return tag_value
    
    if isinstance(tag_value, str):
        try:
            # "['드라이브', '거리']" 형태 파싱
            parsed = ast.literal_eval(tag_value)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except:
            # 파싱 실패시 쉼표로 분할
            return [tag.strip() for tag in tag_value.split(',') if tag.strip()]
    
    return []

def insert_recommendations(image_id, recommendations_data):
    """추천 음악 데이터를 데이터베이스에 삽입"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for rank, song in enumerate(recommendations_data, 1):
                # 태그 데이터 파싱
                상황태그 = parse_tag_array(song.get('상황태그', []))
                감성태그 = parse_tag_array(song.get('감성태그', []))
                시간대태그 = parse_tag_array(song.get('시간대태그', []))
                스타일태그 = parse_tag_array(song.get('스타일태그', []))
                날씨태그 = parse_tag_array(song.get('날씨태그', []))
                계절태그 = parse_tag_array(song.get('계절태그', []))

                similarity_value = song.get('similarity') or song.get('유사도', 0.0)
                if similarity_value is None:
                    similarity_value = 0.0
                
                cur.execute("""
                    INSERT INTO recommendations (
                        image_id, rank, title, artist, genre, similarity,
                        tag_situation, tag_emotion, tag_time, tag_style, tag_weather, tag_season
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    image_id,
                    rank,
                    song.get('곡명', ''),
                    song.get('가수', ''),
                    song.get('장르', ''),
                    float(similarity_value),
                    상황태그,
                    감성태그,
                    시간대태그,
                    스타일태그,
                    날씨태그,
                    계절태그
                ))
            
            conn.commit()
            logger.info(f"추천 음악 데이터 삽입 완료: image_id={image_id}, 곡 수={len(recommendations_data)}")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"추천 음악 데이터 삽입 실패: {e}")
        raise
    finally:
        conn.close()

# ✅ 새로운 로컬 이미지 저장 함수
def save_image_locally(file_bytes, original_filename):
    try:
        processed_bytes = validate_and_process_image(file_bytes)
        unique_filename = f"img_{uuid.uuid4().hex}_{secure_filename(original_filename)}"
        if not unique_filename.lower().endswith('.jpg'):
            unique_filename = unique_filename.rsplit('.', 1)[0] + '.jpg'

        # 로컬 저장 경로 (파일 시스템 기준)
        local_file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(local_file_path, 'wb') as f:
            f.write(processed_bytes)

        logger.info(f"로컬 이미지 저장 완료: {local_file_path}")

        # ✅ 수정: DB에는 웹 접근 가능한 경로만 저장
        web_path = f"/static/uploads/{unique_filename}"

        return local_file_path, web_path, unique_filename  # ✅ unique_filename도 반환
    
    except Exception as e:
        logger.error(f"로컬 이미지 저장 실패: {e}")
        raise Exception(f"로컬 이미지 저장 실패: {str(e)}")

def save_databricks_result_to_db(web_file_path, databricks_result):  # ✅ 웹 경로 받음
    """Databricks 결과를 데이터베이스에 저장"""
    try:
        # 1. 이미지 정보 삽입 (웹 경로 저장)
        image_id = insert_image_data(web_file_path)  # ✅ 웹 경로 전달
        
        # 2. 이미지 태그 삽입
        if 'tags' in databricks_result:
            insert_image_tags(image_id, databricks_result['tags'])
        
        # 3. 추천 음악 삽입
        if 'recommendations' in databricks_result:
            insert_recommendations(image_id, databricks_result['recommendations'])
        
        logger.info(f"Databricks 결과 DB 저장 완료: image_id={image_id}, web_path={web_file_path}")
        return image_id
        
    except Exception as e:
        logger.error(f"Databricks 결과 DB 저장 실패: {e}")
        raise

def get_recommendations_by_image_id(image_id):
    """이미지 ID로 추천 음악 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, i.file_name, i.upload_time, t.*
                FROM recommendations r
                JOIN images i ON r.image_id = i.id
                LEFT JOIN image_tags t ON r.image_id = t.image_id
                WHERE r.image_id = %s
                ORDER BY r.rank
            """, (image_id,))
            
            results = cur.fetchall()

            if results:
                print(f"🔍 DB 조회 결과 첫 번째 레코드:")
                print(f"   타입: {type(results[0])}")
                print(f"   키들: {list(results[0].keys()) if hasattr(results[0], 'keys') else 'keys() 없음'}")
                print(f"   내용: {dict(results[0])}")

            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"추천 음악 조회 실패: {e}")
        raise
    finally:
        conn.close()

def get_recent_recommendations(limit=10):
    """최근 추천 음악 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT ON (r.image_id) r.image_id, i.file_name, i.upload_time,
                       COUNT(r.id) as recommendation_count
                FROM recommendations r
                JOIN images i ON r.image_id = i.id
                GROUP BY r.image_id, i.file_name, i.upload_time
                ORDER BY i.upload_time DESC
                LIMIT %s
            """, (limit,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"최근 추천 음악 조회 실패: {e}")
        raise
    finally:
        conn.close()

def is_audio_url_playable(audio_url, timeout=5):
    try:
        headers = {
            "Range": "bytes=0-65535"
        }
        resp = requests.get(audio_url, headers=headers, timeout=timeout, stream=True)
        if resp.status_code in (200, 206) and resp.headers.get("Content-Type", "").startswith("audio"):
            return True
    except Exception as e:
        print(f"오디오 url 재생 불가: {e}")
    return False

def save_result_pickle(result, filename=PICKLE_FILENAME):
    """추천 결과를 pickle 파일로 저장"""
    with open(filename, "wb") as f:
        pickle.dump(result, f)

def load_result_pickle(filename=PICKLE_FILENAME):
    """pickle 파일에서 추천 결과 불러오기"""
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    return None

def search_youtube_video_url_list(query, max_results=5):
    """검색어로 유튜브 영상 URL 리스트 반환"""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        video_data = []
        for item in response["items"]:
            # videoId 없는 경우 무시 (KeyError 방지)
            if "videoId" not in item["id"]:
                continue
            video_data.append({
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        # Topic 채널 > Official/MV > 나머지 순 정렬
        sorted_data = []
        sorted_data += [v for v in video_data if v["channel"].endswith(" - Topic")]
        sorted_data += [v for v in video_data if any(k in v["title"].lower() for k in ["official", "mv", "music video"]) and v not in sorted_data]
        sorted_data += [v for v in video_data if v not in sorted_data]
        return [v["url"] for v in sorted_data]
    except Exception as e:
        print(f"검색 실패: {e}")
        return []

def get_valid_youtube_audio_url(video_url_list):
    """
    유튜브 영상 URL 리스트에서 오디오 추출 성공 + 실제 브라우저 재생 가능한 첫 번째 URL 반환
    """
    for url in video_url_list:
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'skip_download': True,
                'cookiefile': './cookies.txt',  # 필요시만
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info.get('url')
                # 실제 audio 스트림이 재생 가능한지 검증
                if audio_url and is_audio_url_playable(audio_url):
                    return audio_url
        except Exception as e:
            print(f"오디오 추출 실패: {e}")
            continue
    return None

def add_audio_urls_to_recommendations(recommendations, max_workers=5):
    def fetch_audio_url(song_info):
        song, index = song_info
        try:
            artist = song.get('가수', '').strip()
            title = song.get('곡명', '').strip()
            if not artist or not title:
                return None
            
            search_query = f"{artist} {title}".strip()
            video_url_list = search_youtube_video_url_list(search_query, max_results=5)
            audio_url = get_valid_youtube_audio_url(video_url_list)
            
            if audio_url and test_audio_url(audio_url):
                song['audio_url'] = audio_url
                return song  # 성공한 곡만 반환
            else:
                return None  # 실패 시 None 반환
        except Exception as e:
            return None

    song_infos = [(song, i) for i, song in enumerate(recommendations)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_audio_url, song_infos))

    # 실패(None)인 곡은 제외
    valid_recommendations = [song for song in results if song is not None]
    return valid_recommendations

def test_audio_url(audio_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(audio_url, headers=headers, stream=True, timeout=10)
        if r.status_code == 200 and "audio" in r.headers.get("Content-Type", ""):
            # 실제 스트림 일부를 읽어서 재생 가능 여부 가늠
            next(r.iter_content(1024*64))
            return True
        else:
            return False
    except Exception as e:
        print(f"오디오 다운로드 테스트 실패: {e}")
        return False

# ✅ 커스텀 필터 추가
@app.template_filter('split')
def split_filter(value, delimiter=','):
    """문자열을 구분자로 분할하는 필터"""
    if isinstance(value, str):
        return value.split(delimiter)
    return value

@app.template_filter('parse_list')
def parse_list_filter(value):
    """리스트 형태의 문자열을 파싱하는 필터"""
    if isinstance(value, str):
        # "['드라이브']" 형태를 처리
        try:
            return ast.literal_eval(value)
        except:
            # 파싱 실패시 문자열을 직접 처리
            return value.replace("[", "").replace("]", "").replace("'", "").split(", ")
    return value if isinstance(value, list) else []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_and_process_image(file_bytes):
    """이미지 파일 검증 및 EXIF 회전 처리 포함"""
    try:
        img = Image.open(BytesIO(file_bytes))

        # EXIF Orientation 처리
        try:
            exif = img._getexif()
            if exif is not None:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                orientation_value = exif.get(orientation, None)

                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
        except Exception as e:
            print(f"EXIF 회전 처리 실패: {e}")

        # RGB로 변환
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        # 크기 제한
        max_size = (1024, 1024)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 저장
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()

    except Exception as e:
        raise ValueError(f"이미지 처리 실패: {str(e)}")

# ✅ 완전히 수정된 DBFS에 이미지 저장 함수
def save_file_to_dbfs(file_bytes, filename):
    try:
        # 이미지 검증 및 처리
        processed_bytes = validate_and_process_image(file_bytes)
        
        unique_filename = f"img_{uuid.uuid4().hex}_{secure_filename(filename)}"
        # 확장자를 .jpg로 통일
        if not unique_filename.lower().endswith('.jpg'):
            unique_filename = unique_filename.rsplit('.', 1)[0] + '.jpg'
        
        dbfs_path = f"/FileStore/uploads/{unique_filename}"
        
        headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}
        
        # 파일 크기 체크 (1MB 이하는 put API, 이상은 create-add-close)
        if len(processed_bytes) <= 1024 * 1024:  # 1MB 이하
            # POST /api/2.0/dbfs/put 사용 (간단한 업로드)
            encoded_data = base64.b64encode(processed_bytes).decode('utf-8')
            
            response = requests.post(
                f"{DATABRICKS_HOST}/api/2.0/dbfs/put",
                headers=headers,
                json={
                    "path": dbfs_path,
                    "contents": encoded_data,
                    "overwrite": True
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"DBFS put 실패: {response.text}")
                
        else:  # 1MB 초과 (청크 업로드)
            # 1. create handle
            create_response = requests.post(
                f"{DATABRICKS_HOST}/api/2.0/dbfs/create",
                headers=headers,
                json={"path": dbfs_path, "overwrite": True}
            )
            
            if create_response.status_code != 200:
                raise Exception(f"DBFS create 실패: {create_response.text}")
                
            handle = create_response.json()["handle"]

            try:
                # 2. add blocks
                chunk_size = 1024 * 1024  # 1MB 청크
                
                for i in range(0, len(processed_bytes), chunk_size):
                    chunk = processed_bytes[i:i + chunk_size]
                    encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                    
                    add_response = requests.post(
                        f"{DATABRICKS_HOST}/api/2.0/dbfs/add-block",
                        headers=headers,
                        json={
                            "handle": handle,
                            "data": encoded_chunk
                        }
                    )
                    
                    if add_response.status_code != 200:
                        raise Exception(f"DBFS add-block 실패: {add_response.text}")

                # 3. close handle
                close_response = requests.post(
                    f"{DATABRICKS_HOST}/api/2.0/dbfs/close",
                    headers=headers,
                    json={"handle": handle}
                )
                
                if close_response.status_code != 200:
                    raise Exception(f"DBFS close 실패: {close_response.text}")
                    
            except Exception as e:
                # 실패 시 handle 닫기 시도
                try:
                    requests.post(
                        f"{DATABRICKS_HOST}/api/2.0/dbfs/close",
                        headers=headers,
                        json={"handle": handle}
                    )
                except:
                    pass
                raise e
        
        return dbfs_path
        
    except Exception as e:
        raise Exception(f"파일 저장 실패: {str(e)}")

# 디버깅용 함수
def test_dbfs_connection():
    """DBFS 연결 테스트"""
    try:
        headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}
        
        # DBFS 루트 디렉토리 조회
        response = requests.get(
            f"{DATABRICKS_HOST}/api/2.0/dbfs/list",
            headers=headers,
            params={"path": "/"}
        )
        
        print(f"DBFS 연결 테스트 결과: {response.status_code}")
        print(f"응답: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"DBFS 연결 테스트 실패: {e}")
        return False

# ✅ 수정된 Databricks Job 실행 함수
def run_databricks_job(image_path, selected_genres):
    payload = {
        "job_id": DATABRICKS_JOB_ID,
        "notebook_params": {
            "image_path": image_path,
            "genres": json.dumps(selected_genres)
        }
    }

    headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

    response = requests.post(f"{DATABRICKS_HOST}/api/2.1/jobs/run-now", json=payload, headers=headers)
    response.raise_for_status()
    run_id = response.json()["run_id"]

    # 대기
    max_wait_time = 300  # 5분 최대 대기
    start_time = time.time()
    
    while True:
        if time.time() - start_time > max_wait_time:
            raise Exception("Job 실행 시간 초과")
            
        status_response = requests.get(
            f"{DATABRICKS_HOST}/api/2.1/jobs/runs/get",
            headers=headers,
            params={"run_id": run_id}
        )
        
        status_data = status_response.json()
        status = status_data["state"]["life_cycle_state"]
        
        if status in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
            # 실패한 경우 에러 정보 포함
            if status == "INTERNAL_ERROR":
                raise Exception(f"Databricks Job 실행 실패: {status_data}")
            break
            
        time.sleep(3)

    # ✅ 수정된 부분: 개별 태스크 결과 조회
    try:
        # 먼저 run 정보를 다시 가져와서 tasks 확인
        run_info_response = requests.get(
            f"{DATABRICKS_HOST}/api/2.1/jobs/runs/get",
            headers=headers,
            params={"run_id": run_id}
        )
        
        if run_info_response.status_code != 200:
            raise Exception(f"Run 정보 조회 실패: {run_info_response.text}")
        
        run_info = run_info_response.json()
        
        # tasks가 있는지 확인
        if "tasks" in run_info and run_info["tasks"]:
            # 첫 번째 태스크의 run_id 사용
            task_run_id = run_info["tasks"][0]["run_id"]
            print(f"태스크 run_id 사용: {task_run_id}")
            
            # 개별 태스크 결과 조회
            result_response = requests.get(
                f"{DATABRICKS_HOST}/api/2.1/jobs/runs/get-output",
                headers=headers,
                params={"run_id": task_run_id}
            )
        else:
            # 단일 태스크인 경우 기존 방식 사용
            print("단일 태스크로 감지, 기존 방식 사용")
            result_response = requests.get(
                f"{DATABRICKS_HOST}/api/2.1/jobs/runs/get-output",
                headers=headers,
                params={"run_id": run_id}
            )
        
        if result_response.status_code != 200:
            raise Exception(f"결과 조회 실패: {result_response.text}")
        
        result_data = result_response.json()
        
        # notebook_output이 없는 경우 처리
        if "notebook_output" not in result_data:
            raise Exception(f"노트북 출력이 없습니다: {result_data}")
        
        result = result_data["notebook_output"].get("result", "{}")

        try:
            parsed_result = json.loads(result)
            
            # ✅ 수정: error 필드에 실제 결과가 있는지 확인
            if "error" in parsed_result and isinstance(parsed_result["error"], str):
                try:
                    # error 필드를 JSON으로 파싱해보기
                    potential_result = json.loads(parsed_result["error"])
                    if "recommendations" in potential_result and "tags" in potential_result:
                        print("✅ error 필드에서 실제 결과 발견!")
                        return potential_result
                except json.JSONDecodeError:
                    # error 필드가 JSON이 아니면 실제 에러로 처리
                    raise Exception(f"Databricks 처리 에러: {parsed_result['error']}")

            # 정상적인 결과 확인
            if "recommendations" in parsed_result and "tags" in parsed_result:
                return parsed_result
            
            # 그 외의 경우는 에러로 처리
            raise Exception(f"예상하지 못한 결과 형식: {parsed_result}")
            
        except json.JSONDecodeError:
            raise Exception(f"결과 파싱 실패: {result}")
            
    except Exception as e:
        print(f"결과 조회 중 에러: {str(e)}")
        raise

# 추천 결과 전처리 함수
def process_recommendation_result(result):
    """추천 결과를 템플릿에서 사용하기 쉽게 전처리 + YouTube 오디오 URL 추가"""
    try:
        if 'recommendations' in result:
            # 기존 태그 전처리
            for song in result['recommendations']:
                print(f"곡명: {song.get('곡명')}, 오디오 URL: {song.get('audio_url')}")
                tag_fields = ['상황태그', '감성태그', '시간대태그', '스타일태그', '날씨태그', '계절태그']
                
                for field in tag_fields:
                    if field in song:
                        tag_value = song[field]
                        if isinstance(tag_value, str):
                            try:
                                parsed_tags = ast.literal_eval(tag_value)
                                song[f'parsed_{field}'] = parsed_tags if isinstance(parsed_tags, list) else []
                            except:
                                song[f'parsed_{field}'] = []
                        else:
                            song[f'parsed_{field}'] = tag_value if isinstance(tag_value, list) else []
            
            # ✅ 수정된 YouTube 오디오 URL 추가 (순서 보존)
            print("🎵 YouTube 오디오 URL 가져오는 중...")
            result['recommendations'] = add_audio_urls_to_recommendations(
                result['recommendations'], 
                max_workers=3  # 너무 많은 동시 요청 방지
            )
            
            # 통계 출력
            total_songs = len(result['recommendations'])
            playable_songs = sum(1 for song in result['recommendations'] if song.get('has_audio', False))
            print(f"✅ YouTube 오디오 URL 추가 완료: {playable_songs}/{total_songs}곡 재생 가능")
            print(result)
        return result
    except Exception as e:
        print(f"결과 전처리 실패: {str(e)}")
        return result

def convert_db_to_template_format(db_recommendations):
    """DB에서 가져온 추천 데이터를 템플릿에서 사용할 형식으로 변환"""
    if not db_recommendations:
        return None
    
    # 첫 번째 레코드에서 이미지 정보와 태그 추출
    first_record = db_recommendations[0]
    tag_fields_mapping = {
        '상황': 'tag_situation',
        '감성': 'tag_emotion', 
        '시간대': 'tag_time',
        '스타일': 'tag_style',
        '날씨': 'tag_weather',
        '계절': 'tag_season'
    }
    
    # 태그 정보 구성
    tags = {}
    for kr_field, db_field in tag_fields_mapping.items():
        if db_field in first_record and first_record[db_field]:
            tags[kr_field] = first_record[db_field]
    
    # 추천 음악 리스트 구성
    recommendations = []
    for record in db_recommendations:
        similarity_score = float(record.get('similarity', 0.0) if record.get('similarity') is not None else 0.0)

        song = {
            '곡명': record.get('title', ''),
            '가수': record.get('artist', ''),
            '장르': record.get('genre', ''),
            'similarity': similarity_score, 
            '유사도': similarity_score,
            'audio_url': None
        }
    
        # 태그 정보 추가
        tag_fields_mapping_song = {
            '상황태그': 'tag_situation',
            '감성태그': 'tag_emotion',
            '시간대태그': 'tag_time',
            '스타일태그': 'tag_style',
            '날씨태그': 'tag_weather',
            '계절태그': 'tag_season'
        }
        
        for kr_field, db_field in tag_fields_mapping_song.items():
            if db_field in record and record[db_field]:
                song[kr_field] = record[db_field]
                song[f'parsed_{kr_field}'] = parse_tag_array(record[db_field])
        recommendations.append(song)
    
    # YouTube 오디오 URL 추가
    recommendations = add_audio_urls_to_recommendations(recommendations)
    
    # ✅ 수정된 이미지 경로 처리
    db_path = first_record.get('file_name', '')  # DB에서 웹 경로 가져옴
    
    # DB 경로에서 파일명만 추출
    if db_path.startswith('/static/uploads/'):
        filename = db_path.replace('/static/uploads/', '')
    elif db_path.startswith('static/uploads/'):
        filename = db_path.replace('static/uploads/', '')
    elif db_path.startswith('uploads/'):
        filename = db_path.replace('uploads/', '')
    else:
        filename = db_path
    
    result = {
        'tags': tags,
        'recommendations': recommendations,
        'image_info': {
            'filename': f'uploads/{filename}',  # ✅ url_for용 경로 (static/ 제외)
            'upload_time': first_record.get('upload_time', ''),
            'image_id': first_record.get('image_id', ''),
            'web_url': f'/static/uploads/{filename}',  # ✅ 직접 접근용 경로
            'static_filename': f'uploads/{filename}'  # ✅ 새로 추가: url_for용
        }
    }
    return result

# ✅ 메인 페이지
@app.route('/home/', methods=['GET', 'POST'])
def home():
    error = None
    if request.method == 'POST':
        try:
            file = request.files.get('image')
            selected_genres_str = request.form.get('selected_genres')
            selected_genres = selected_genres_str.split(",") if selected_genres_str else []

            if not file or file.filename == '':
                error = "이미지 파일이 선택되지 않았습니다."
                return render_template('home.html', genres=genres, error=error)

            if not allowed_file(file.filename):
                error = "지원하지 않는 파일 형식입니다."
                return render_template('home.html', genres=genres, error=error)

            if not selected_genres:
                error = "최소 1개의 장르를 선택해주세요."
                return render_template('home.html', genres=genres, error=error)

            image_bytes = file.read()

            # ✅ 수정된 부분
            local_path, web_path, unique_filename = save_image_locally(image_bytes, file.filename)

            session['local_file_path'] = local_path
            session['image_web_path'] = web_path  # ✅ 웹 경로 저장
            session['unique_filename'] = unique_filename  # ✅ 파일명만 저장
            session['filename'] = file.filename
            session['selected_genres'] = selected_genres

            return redirect(url_for('loading'))

        except Exception as e:
            traceback.print_exc()
            error = f"처리 중 에러 발생: {str(e)}"

    return render_template('home.html', genres=genres, error=error)

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/process_recommendation')
def process_recommendation():
    try:
        local_file_path = session.get('local_file_path')
        web_path = session.get('image_web_path')  # ✅ 웹 경로 사용
        filename = session.get('filename')
        selected_genres = session.get('selected_genres')

        if not local_file_path or not web_path or not filename or not selected_genres:
            return jsonify({'success': False, 'message': '세션 정보가 부족합니다.'})

        with open(local_file_path, 'rb') as f:
            image_bytes = f.read()

        dbfs_path = save_file_to_dbfs(image_bytes, filename)
        result = run_databricks_job(dbfs_path, selected_genres)
        processed_result = process_recommendation_result(result)
        
        # ✅ 웹 경로를 DB에 저장
        image_id = save_databricks_result_to_db(web_path, processed_result)
        save_result_pickle(processed_result)

        session['current_image_id'] = image_id
        session['current_image_path'] = local_file_path

        return jsonify({'success': True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/recommendation/', methods=['GET'])
def recommendation():
    try:
        # URL 파라미터로 image_id가 전달된 경우
        image_id = request.args.get('image_id')
        
        if image_id:
            # DB에서 특정 이미지의 추천 결과 조회
            recommendations = get_recommendations_by_image_id(image_id)
            if recommendations:
                # DB 데이터를 템플릿용으로 변환
                result = convert_db_to_template_format(recommendations)
                
                logger.debug(f"템플릿에 전달되는 result 구조: {result}")
                return render_template('view.html', result=result, image_id=image_id)
        
        # 세션에서 현재 이미지 ID 확인
        current_image_id = session.get('current_image_id')
        if current_image_id:
            recommendations = get_recommendations_by_image_id(current_image_id)
            if recommendations:
                result = convert_db_to_template_format(recommendations)
                return render_template('view.html', result=result, image_id=current_image_id)
        
        # 둘 다 없으면 pickle에서 가져오기 (기존 방식)
        result = load_result_pickle()
        
        # ✅ pickle 결과에도 이미지 경로 추가 (세션에서 가져오기)
        if result and session.get('image_web_path'):
            if 'image_info' not in result:
                result['image_info'] = {}
            
            # 세션에서 가져온 웹 경로 처리
            web_path = session.get('image_web_path')  # /static/uploads/filename.jpg
            if web_path.startswith('/static/uploads/'):
                filename = web_path.replace('/static/uploads/', '')
            elif web_path.startswith('static/uploads/'):
                filename = web_path.replace('static/uploads/', '')
            else:
                filename = web_path
            
            result['image_info']['web_url'] = f'/static/uploads/{filename}'
            result['image_info']['static_filename'] = f'uploads/{filename}'  # ✅ url_for용
        
        return render_template('view.html', result=result)
        
    except Exception as e:
        logger.error(f"플레이리스트 조회 실패: {e}")
        flash("플레이리스트를 불러오는데 실패했습니다.", "error")
        return redirect(url_for('home'))

# 이미지 파일과 image_id 매핑
def get_image_mapping():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, file_name
                FROM images
                ORDER BY upload_time DESC
                LIMIT 20
            """)
            results = cur.fetchall()
            return {r['file_name']: r['id'] for r in results}
    except Exception as e:
        logger.error(f"이미지 매핑 조회 실패: {e}")
        return {}
    finally:
        conn.close()

def fetch_archive_photos(limit: int | None = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT i.id AS image_id,
                       i.file_name,
                       p.rank,
                       p.title,
                       p.artist,
                       COALESCE(p.genre, '') AS genre,
                       p.tag_situation,
                       p.tag_emotion,
                       p.tag_time,
                       p.tag_style,
                       p.tag_weather,
                       p.tag_season
                FROM images i
                LEFT JOIN recommendations p ON p.image_id = i.id
                ORDER BY i.upload_time DESC, p.rank
                {'' if not limit else 'LIMIT %s'}
            """, (limit,) if limit else ())
            rows = cur.fetchall()
 
        photo_dict = defaultdict(lambda: {"file_name": "", "songs": [], "tags": set()})
 
        for r in rows:
            pid = r["image_id"]
            photo_dict[pid]["file_name"] = r["file_name"]
 
            # 추천곡 리스트 생성
            if r["title"]:  # playlist에 곡이 존재
                photo_dict[pid]["songs"].append({
                    "title":  r["title"],
                    "artist": r["artist"],
                    "genre":  r["genre"]
                })
 
            # 태그 리스트 생성
            tag_cols = ["tag_situation", "tag_emotion", "tag_time",
                        "tag_style", "tag_weather", "tag_season"]
            for col in tag_cols:
                tag_values = r.get(col)
                if tag_values:  # TEXT[]
                    photo_dict[pid]["tags"].update(tag_values)
 
        # set → list 변환 & dict → list 변환
        photos = []
        for pid, info in photo_dict.items():
            info["tags"] = list(info["tags"])
            photos.append(info) 
        return photos
 
    except Exception as e:
        logger.error(f"아카이브 데이터 조회 실패: {e}")
        return []
    finally:
        conn.close()
 
@app.route('/archive/')
def archive():
    try:
        photos = fetch_archive_photos()
        image_mapping = get_image_mapping()  # 이미지 ID 매핑 정보 가져오기
        
        for photo in photos:
            fname = photo['file_name']
            
            # ✅ DB에 저장된 경로 형식 확인 및 정규화
            if fname.startswith('/static/uploads/'):
                # '/static/uploads/filename.jpg' 형태
                clean_filename = fname.replace('/static/uploads/', '')
            elif fname.startswith('static/uploads/'):
                # 'static/uploads/filename.jpg' 형태  
                clean_filename = fname.replace('static/uploads/', '')
            elif fname.startswith('/uploads/'):
                # '/uploads/filename.jpg' 형태
                clean_filename = fname.replace('/uploads/', '')
            elif fname.startswith('uploads/'):
                # 'uploads/filename.jpg' 형태
                clean_filename = fname.replace('uploads/', '')
            else:
                # 'filename.jpg' 형태 (순수 파일명)
                clean_filename = fname
            
            # ✅ 웹 접근 가능한 URL 생성
            photo["file_url"] = f"/static/uploads/{clean_filename}"
            
            # ✅ 디버깅을 위한 로그 추가
            logger.info(f"Archive 이미지 경로: DB={fname} -> URL={photo['file_url']}")
            
            # ✅ 이미지 ID 추가 (view 페이지 연결용)
            photo["image_id"] = image_mapping.get(fname, None)

        return render_template('archive.html', photos=photos)
    
    except Exception as e:
        logger.error(f"아카이브 조회 실패: {e}")
        flash("아카이브를 불러오는데 실패했습니다.", "error")
        return render_template('archive.html', photos=[])
    
@app.route('/api/recommendations/<int:image_id>')
def get_recommendations_api(image_id):
    """특정 이미지의 추천 음악을 JSON으로 반환"""
    try:
        recommendations = get_recommendations_by_image_id(image_id)
        if not recommendations:
            return {"error": "추천 음악을 찾을 수 없습니다."}, 404
        
        result = convert_db_to_template_format(recommendations)
        return result
    except Exception as e:
        logger.error(f"API 추천 조회 실패: {e}")
        return {"error": "서버 오류가 발생했습니다."}, 500
    
def handle_database_error(error_msg, redirect_route='home'):
    """데이터베이스 에러 공통 처리"""
    logger.error(error_msg)
    flash("데이터베이스 오류가 발생했습니다.", "error")
    return redirect(url_for(redirect_route))

# 세션 정리 함수
@app.route('/clear-session')
def clear_session():
    """세션 정리 (디버깅용)"""
    session.clear()
    return redirect(url_for('home'))

# ✅ 루트 경로
@app.route('/')
def index():
    return render_template('home.html', genres=genres, error=None)

if __name__ == '__main__':
    # DBFS 연결 테스트 (선택적)
    print("🔄 DBFS 연결 테스트 중...")
    if test_dbfs_connection():
        print("✅ DBFS 연결 성공")
    else:
        print("❌ DBFS 연결 실패 - 토큰이나 호스트 확인 필요")
        print("⚠️  애플리케이션을 시작하지만 파일 업로드가 실패할 수 있습니다.")
    
    print("🚀 Flask 애플리케이션 시작...")
    app.run(host='0.0.0.0', port=5000, debug=True)
