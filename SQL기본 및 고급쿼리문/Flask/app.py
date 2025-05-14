from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import DictCursor

load_dotenv(".env")
app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    conn.autocommit = True
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('''
        SELECT id, title, author, created_at, view_count, like_count
        FROM board.posts
        ORDER BY created_at DESC
    ''')
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        content = request.form['content']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO board.posts (title, author, content, created_at, view_count, like_count)
            VALUES (%s, %s, %s, NOW(), 0, 0)
        ''', (title, author, content))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/view/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    cursor.execute('''
        SELECT id, title, author, content, created_at, view_count, like_count
        FROM board.posts
        WHERE id = %s
    ''', (post_id,))
    post = cursor.fetchone()

    # 조회수 증가
    cursor.execute('UPDATE board.posts SET view_count = view_count + 1 WHERE id = %s', (post_id,))

    # 댓글 불러오기
    cursor.execute('''
        SELECT author, content, created_at
        FROM board.comments
        WHERE post_id = %s
        ORDER BY created_at ASC
    ''', (post_id,))
    comments = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return render_template('view.html', post=post, comments=comments, liked=False)


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute('''
            UPDATE board.posts
            SET title = %s, content = %s
            WHERE id = %s
        ''', (title, content, post_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_post', post_id=post_id))

    cursor.execute('SELECT id, title, author, content FROM board.posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit.html', post=post)

@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_ip = request.remote_addr
    conn = get_db_connection()
    cursor = conn.cursor()

    # 좋아요 중복 여부 확인
    cursor.execute('''
        SELECT 1 FROM board.likes WHERE post_id = %s AND user_ip = %s
    ''', (post_id, user_ip))
    already_liked = cursor.fetchone()

    if not already_liked:
        cursor.execute('''
            INSERT INTO board.likes (post_id, user_ip, created_at)
            VALUES (%s, %s, NOW())
        ''', (post_id, user_ip))

        cursor.execute('''
            UPDATE board.posts
            SET like_count = like_count + 1
            WHERE id = %s
        ''', (post_id,))

    # 새 like_count 조회
    cursor.execute('SELECT like_count FROM board.posts WHERE id = %s', (post_id,))
    like_count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'like_count': like_count})


@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM board.posts WHERE id = %s', (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    author = request.form['author']
    content = request.form['content']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO board.comments (post_id, author, content, created_at)
        VALUES (%s, %s, %s, NOW())
    ''', (post_id, author, content))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('view_post', post_id=post_id))

@app.route('/fms-result')
def fms_result():
    keyword = request.args.get('keyword', '')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    if keyword:
        cursor.execute('''
            SELECT * FROM public.total_result
            WHERE 육계번호 ILIKE %s OR 품종 ILIKE %s OR 고객사 ILIKE %s
            ORDER BY 도착일 DESC
        ''', [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    else:
        cursor.execute('SELECT * FROM public.total_result ORDER BY 도착일 DESC')

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('fms_result.html', results=results, keyword=keyword)

@app.route('/check_health/<chick_no>')
def check_health(chick_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT detect_unhealthy_chick(%s)", (chick_no,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    message = '건강 상태가 양호합니다 😊' if not result else '건강에 이상이 있어요. 확인이 필요합니다 ⚠️'
    return jsonify({'message': message})

@app.route('/fms-create', methods=['GET', 'POST'])
def fms_create():
    if request.method == 'POST':
        data = (
            request.form['육계번호'], request.form['품종'], request.form['종란무게'], request.form['체온'],
            request.form['호흡수'], request.form['호수'], request.form['부적합여부'],
            request.form['주문번호'], request.form['고객사'], request.form['도착일'], request.form['도착지']
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO public.total_result VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', data)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('fms_result'))
    return render_template('fms_create.html')

@app.route('/fms-edit/<chick_no>', methods=['GET', 'POST'])
def fms_edit(chick_no):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    if request.method == 'POST':
        cursor.execute('''
            UPDATE public.total_result
            SET 품종=%s, 종란무게=%s, 체온=%s, 호흡수=%s, 호수=%s,
                부적합여부=%s, 주문번호=%s, 고객사=%s, 도착일=%s, 도착지=%s
            WHERE 육계번호=%s
        ''', (
            request.form['품종'], request.form['종란무게'], request.form['체온'], request.form['호흡수'],
            request.form['호수'], request.form['부적합여부'], request.form['주문번호'],
            request.form['고객사'], request.form['도착일'], request.form['도착지'], chick_no
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('fms_result'))

    cursor.execute('SELECT * FROM public.total_result WHERE 육계번호 = %s', (chick_no,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('fms_edit.html', row=row)

@app.route('/fms-delete/<chick_no>', methods=['POST'])
def fms_delete(chick_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM public.total_result WHERE 육계번호 = %s', (chick_no,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('fms_result'))



if __name__ == '__main__':
    app.run(debug=True)
