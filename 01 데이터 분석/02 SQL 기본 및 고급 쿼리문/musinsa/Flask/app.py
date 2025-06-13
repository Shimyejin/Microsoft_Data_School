from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Flash 메시지에 필요

# DB 연결 함수
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    conn.set_session(autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SET search_path TO musinsa;")
    return conn

# -------------------------
# No.30 Closet (위시리스트)
# -------------------------
@app.route('/')
def closet():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 대분류 필터링
    selected_main = request.args.get('main_category', '전체')

    query = """
        SELECT w.id AS wishlist_id, p.*, w.memo, w.created_at, c.main_category
        FROM wishlist w
        JOIN products p ON w.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
    """
    params = []
    if selected_main != '전체':
        query += " WHERE c.main_category = %s"
        params.append(selected_main)

    query += " ORDER BY w.created_at DESC"
    cursor.execute(query, params)
    items = cursor.fetchall()

    cursor.execute("SELECT DISTINCT main_category FROM categories ORDER BY main_category")
    main_categories = [row['main_category'] for row in cursor.fetchall()]

    conn.close()
    return render_template('closet.html', items=items, main_categories=main_categories, selected_main=selected_main)

# 위시리스트 삭제
@app.route('/wishlist/delete/<int:wishlist_id>', methods=['POST'])
def delete_wishlist_item(wishlist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wishlist WHERE id = %s", (wishlist_id,))
    conn.commit()
    conn.close()
    flash("상품이 위시리스트에서 삭제되었습니다.")
    return redirect(url_for('closet'))

# -------------------------
# Outlet Dive (필터링)
# -------------------------
@app.route('/outlet', methods=['GET'])
def outlet():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 카테고리 목록 로드
    cursor.execute("SELECT main_category, sub_category FROM categories ORDER BY category_id")
    rows = cursor.fetchall()
    category_dict = {}
    for row in rows:
        category_dict.setdefault(row['main_category'], []).append(row['sub_category'])

    # 필터 파라미터
    main_category = request.args.get('main_category', '의류')
    category = request.args.get('category', '상의')
    brand = request.args.get('brand')
    discount_min = request.args.get('discount_min', type=int)
    price_max = request.args.get('price_max', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 60
    offset = (page - 1) * per_page

    # 필터 쿼리 구성
    base_query = """
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE c.main_category = %s AND c.sub_category = %s
    """
    values = [main_category, category]
    filters = ""

    if brand:
        filters += " AND b.brand_name ILIKE %s"
        values.append(f"%{brand}%")
    if discount_min:
        filters += " AND p.discount_rate >= %s"
        values.append(discount_min)
    if price_max:
        filters += " AND p.discount_price <= %s"
        values.append(price_max)

    # 총 페이지 수
    count_query = "SELECT COUNT(*) " + base_query + filters
    cursor.execute(count_query, values)
    total_count = cursor.fetchone()['count']
    total_pages = (total_count + per_page - 1) // per_page

    # 실제 상품 데이터
    product_query = "SELECT p.* " + base_query + filters + " ORDER BY p.product_id DESC LIMIT %s OFFSET %s"
    cursor.execute(product_query, values + [per_page, offset])
    products = cursor.fetchall()

    # 위시리스트에 담긴 product_id 불러오기
    cursor.execute("SELECT product_id FROM wishlist")
    wishlist_ids = set(row['product_id'] for row in cursor.fetchall())

    conn.close()

    return render_template(
        'outlet.html',
        products=products,
        category_dict=category_dict,
        current_main=main_category,
        current_sub=category,
        page=page,
        total_pages=total_pages,
        wishlist_ids=wishlist_ids
    )

# -------------------------
# 위시리스트 추가
# -------------------------
@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 중복 방지
    cursor.execute("SELECT 1 FROM wishlist WHERE product_id = %s", (product_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO wishlist (product_id) VALUES (%s)", (product_id,))
        flash("상품이 위시리스트에 추가되었습니다!")
    else:
        flash("이미 위시리스트에 있는 상품입니다!")

    conn.commit()
    conn.close()
    return redirect(url_for('outlet'))

# -------------------------
# Analytics Splash (시각화)
# -------------------------
@app.route('/charts')
def charts():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 🔹 brands 기준 평균 할인율 (products 전체 기준)
    cursor.execute("""
        SELECT b.brand_name,
               ROUND(AVG(p.discount_rate), 1) AS avg_discount
        FROM products p
        JOIN brands b ON p.brand_id = b.brand_id
        WHERE p.discount_rate IS NOT NULL
        GROUP BY b.brand_name
        ORDER BY avg_discount DESC
        LIMIT 10
    """)
    discount_data = cursor.fetchall()

    # 🔹 할인율 구간별 평균 리뷰 수 (products 전체 기준)
    cursor.execute("""
        SELECT width_bucket(p.discount_rate, 0, 100, 10) AS bucket,
               ROUND(AVG(p.review_count), 1) AS avg_review
        FROM products p
        WHERE p.discount_rate IS NOT NULL AND p.review_count IS NOT NULL
        GROUP BY bucket
        ORDER BY bucket
    """)
    review_by_discount = cursor.fetchall()

    conn.close()
    return render_template(
        'charts.html',
        discount_data=discount_data,
        review_by_discount=review_by_discount
    )

@app.route('/wishlist/memo', methods=['POST'])
def update_memo():
    wishlist_id = request.form.get('wishlist_id')
    memo = request.form.get('memo')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE wishlist SET memo = %s WHERE id = %s", (memo, wishlist_id))
    conn.commit()
    conn.close()
    flash("메모가 저장되었습니다.")
    return redirect(url_for('closet'))

# -------------------------
# 실행
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
