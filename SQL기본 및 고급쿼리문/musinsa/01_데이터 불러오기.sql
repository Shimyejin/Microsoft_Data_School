CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    main_category VARCHAR(50),
    sub_category VARCHAR(50)
);

CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name TEXT,
    category_id INTEGER REFERENCES categories(category_id),
    brand_id INTEGER REFERENCES brands(brand_id),
    original_price INTEGER,
    discount_price INTEGER,
    discount_rate INTEGER,
    review_count INTEGER,
    review_score INTEGER
);

CREATE TABLE wishlist (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES musinsa.products(product_id),
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
