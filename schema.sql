-- ═══════════════════════════════════════════════════════════════════
-- ShopVerse E-Commerce Platform — PostgreSQL Schema
-- DBMS Semester Project | CYS 2024
-- Students: Ahmad Ali Khan, Abdullah Kaleem, Muhammad Danish, Abbas Alamgir
-- ═══════════════════════════════════════════════════════════════════
-- All tables satisfy 3NF (Third Normal Form).
-- Run: psql -U postgres -d ecommerce_db -f schema.sql
-- ═══════════════════════════════════════════════════════════════════

-- Drop existing tables (safe re-run)
DROP TABLE IF EXISTS wishlist          CASCADE;
DROP TABLE IF EXISTS review            CASCADE;
DROP TABLE IF EXISTS payment           CASCADE;
DROP TABLE IF EXISTS order_item        CASCADE;
DROP TABLE IF EXISTS "order"           CASCADE;
DROP TABLE IF EXISTS cart_item         CASCADE;
DROP TABLE IF EXISTS cart              CASCADE;
DROP TABLE IF EXISTS product_image     CASCADE;
DROP TABLE IF EXISTS product           CASCADE;
DROP TABLE IF EXISTS category          CASCADE;
DROP TABLE IF EXISTS address           CASCADE;
DROP TABLE IF EXISTS vendor_profile    CASCADE;
DROP TABLE IF EXISTS user_profile      CASCADE;

-- ─────────────────────────────────────────────────
-- 1. USER PROFILE  (extends Django auth_user)
-- ─────────────────────────────────────────────────
CREATE TABLE user_profile (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    role        VARCHAR(10) NOT NULL DEFAULT 'customer'
                    CHECK (role IN ('customer', 'vendor', 'admin')),
    phone       VARCHAR(20)  DEFAULT '',
    avatar      VARCHAR(255) DEFAULT NULL,
    
);

COMMENT ON TABLE  user_profile        IS 'Extends Django auth_user with role and contact info.';
COMMENT ON COLUMN user_profile.role   IS 'RBAC: customer | vendor | admin';

-- ─────────────────────────────────────────────────
-- 2. VENDOR PROFILE
-- ─────────────────────────────────────────────────
CREATE TABLE vendor_profile (
    id               SERIAL PRIMARY KEY,
    user_profile_id  INTEGER NOT NULL UNIQUE REFERENCES user_profile(id) ON DELETE CASCADE,
    store_name       VARCHAR(150) NOT NULL,
    store_slug       VARCHAR(160) NOT NULL UNIQUE,
    description      TEXT         DEFAULT '',
    logo             VARCHAR(255) DEFAULT NULL,
    status           VARCHAR(10)  NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending','approved','rejected','suspended')),
    total_sales      NUMERIC(12,2) NOT NULL DEFAULT 0,
    approved_at      TIMESTAMPTZ  DEFAULT NULL,
    approved_by_id   INTEGER      DEFAULT NULL REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE INDEX idx_vendor_status ON vendor_profile(status);

-- ─────────────────────────────────────────────────
-- 3. ADDRESS
-- ─────────────────────────────────────────────────
CREATE TABLE address (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    full_name   VARCHAR(150) NOT NULL,
    street      VARCHAR(255) NOT NULL,
    city        VARCHAR(100) NOT NULL,
    state       VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20)  NOT NULL DEFAULT '',
    country     VARCHAR(100) NOT NULL DEFAULT 'Pakistan',
    is_default  BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_address_user ON address(user_id);

-- ─────────────────────────────────────────────────
-- 4. CATEGORY  (self-referential for sub-categories)
-- ─────────────────────────────────────────────────
CREATE TABLE category (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    slug        VARCHAR(110) NOT NULL UNIQUE,
    description TEXT         DEFAULT '',
    image       VARCHAR(255) DEFAULT NULL,
    parent_id   INTEGER      DEFAULT NULL REFERENCES category(id) ON DELETE SET NULL,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_category_parent ON category(parent_id);

-- ─────────────────────────────────────────────────
-- 5. PRODUCT
-- ─────────────────────────────────────────────────
CREATE TABLE product (
    id           SERIAL PRIMARY KEY,
    vendor_id    INTEGER      NOT NULL REFERENCES vendor_profile(id) ON DELETE CASCADE,
    category_id  INTEGER      DEFAULT NULL REFERENCES category(id) ON DELETE SET NULL,
    name         VARCHAR(200) NOT NULL,
    slug         VARCHAR(220) NOT NULL UNIQUE,
    description  TEXT         NOT NULL DEFAULT '',
    price        NUMERIC(10,2) NOT NULL CHECK (price > 0),
    discount_pct NUMERIC(5,2)  NOT NULL DEFAULT 0
                     CHECK (discount_pct >= 0 AND discount_pct <= 100),
    stock        INTEGER      NOT NULL DEFAULT 0 CHECK (stock >= 0),
    sku          VARCHAR(100) UNIQUE DEFAULT NULL,
    status       VARCHAR(10)  NOT NULL DEFAULT 'active'
                     CHECK (status IN ('active','inactive','sold_out')),
    thumbnail    VARCHAR(255) DEFAULT NULL,
    weight_kg    NUMERIC(6,2) NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_product_slug      ON product(slug);
CREATE INDEX idx_product_status    ON product(status);
CREATE INDEX idx_product_category  ON product(category_id);
CREATE INDEX idx_product_price     ON product(price);
CREATE INDEX idx_product_vendor    ON product(vendor_id);

-- Computed column helper view for discounted price
CREATE OR REPLACE VIEW v_product_price AS
    SELECT id, name, price, discount_pct,
           ROUND(price * (1 - discount_pct / 100.0), 2) AS discounted_price
    FROM product;

-- ─────────────────────────────────────────────────
-- 6. PRODUCT IMAGE
-- ─────────────────────────────────────────────────
CREATE TABLE product_image (
    id         SERIAL PRIMARY KEY,
    product_id INTEGER      NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    image      VARCHAR(255) NOT NULL,
    alt_text   VARCHAR(200) DEFAULT '',
    is_primary BOOLEAN      NOT NULL DEFAULT FALSE,
    "order"    SMALLINT     NOT NULL DEFAULT 0
);

CREATE INDEX idx_product_image_product ON product_image(product_id);

-- ─────────────────────────────────────────────────
-- 7. CART
-- ─────────────────────────────────────────────────
CREATE TABLE cart (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     DEFAULT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    session_key VARCHAR(40) DEFAULT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_cart_owner CHECK (user_id IS NOT NULL OR session_key IS NOT NULL)
);

-- ─────────────────────────────────────────────────
-- 8. CART ITEM
-- ─────────────────────────────────────────────────
CREATE TABLE cart_item (
    id         SERIAL PRIMARY KEY,
    cart_id    INTEGER NOT NULL REFERENCES cart(id)    ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity   INTEGER NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    added_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cart_id, product_id)
);

CREATE INDEX idx_cart_item_cart ON cart_item(cart_id);

-- ─────────────────────────────────────────────────
-- 9. ORDER
-- ─────────────────────────────────────────────────
CREATE TABLE "order" (
    id            SERIAL PRIMARY KEY,
    customer_id   INTEGER      NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    order_number  VARCHAR(20)  NOT NULL UNIQUE,
    status        VARCHAR(15)  NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','confirmed','processing','shipped','delivered','cancelled','refunded')),
    -- Shipping address snapshot (denormalised intentionally for immutability)
    ship_name     VARCHAR(150) NOT NULL,
    ship_street   VARCHAR(255) NOT NULL,
    ship_city     VARCHAR(100) NOT NULL,
    ship_state    VARCHAR(100) NOT NULL,
    ship_postal   VARCHAR(20)  NOT NULL DEFAULT '',
    ship_country  VARCHAR(100) NOT NULL DEFAULT 'Pakistan',
    ship_phone    VARCHAR(20)  DEFAULT '',
    -- Financials
    subtotal      NUMERIC(12,2) NOT NULL,
    shipping_cost NUMERIC(8,2)  NOT NULL DEFAULT 0,
    tax_amount    NUMERIC(8,2)  NOT NULL DEFAULT 0,
    total_amount  NUMERIC(12,2) NOT NULL,
    notes         TEXT          DEFAULT '',
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_customer ON "order"(customer_id);
CREATE INDEX idx_order_status   ON "order"(status);
CREATE INDEX idx_order_number   ON "order"(order_number);

-- ─────────────────────────────────────────────────
-- 10. ORDER ITEM
-- ─────────────────────────────────────────────────
CREATE TABLE order_item (
    id            SERIAL PRIMARY KEY,
    order_id      INTEGER       NOT NULL REFERENCES "order"(id) ON DELETE CASCADE,
    product_id    INTEGER       DEFAULT NULL REFERENCES product(id) ON DELETE SET NULL,
    vendor_id     INTEGER       DEFAULT NULL REFERENCES vendor_profile(id) ON DELETE SET NULL,
    product_name  VARCHAR(200)  NOT NULL,            -- snapshot at time of purchase
    unit_price    NUMERIC(10,2) NOT NULL,            -- snapshot at time of purchase
    quantity      INTEGER       NOT NULL CHECK (quantity >= 1),
    line_total    NUMERIC(12,2) NOT NULL             -- unit_price × quantity
);

CREATE INDEX idx_order_item_order ON order_item(order_id);

-- ─────────────────────────────────────────────────
-- 11. PAYMENT
-- ─────────────────────────────────────────────────
CREATE TABLE payment (
    id             SERIAL PRIMARY KEY,
    order_id       INTEGER      NOT NULL UNIQUE REFERENCES "order"(id) ON DELETE CASCADE,
    method         VARCHAR(20)  NOT NULL
                       CHECK (method IN ('cod','credit_card','debit_card','bank_transfer','easypaisa','jazzcash')),
    status         VARCHAR(10)  NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','completed','failed','refunded')),
    amount         NUMERIC(12,2) NOT NULL,
    transaction_id VARCHAR(200) DEFAULT '',
    paid_at        TIMESTAMPTZ  DEFAULT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE payment IS 'Separated from orders for PCI DSS compliance — no raw card data stored.';

-- ─────────────────────────────────────────────────
-- 12. REVIEW
-- ─────────────────────────────────────────────────
CREATE TABLE review (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES product(id)   ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title       VARCHAR(150) DEFAULT '',
    body        TEXT         NOT NULL,
    is_verified BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, customer_id)    -- one review per customer per product
);

CREATE INDEX idx_review_product ON review(product_id);

-- ─────────────────────────────────────────────────
-- 13. WISHLIST
-- ─────────────────────────────────────────────────
CREATE TABLE wishlist (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES product(id)   ON DELETE CASCADE,
    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, product_id)
);

CREATE INDEX idx_wishlist_customer ON wishlist(customer_id);

-- ═══════════════════════════════════════════════════════════════════
-- KEY SQL QUERIES (for documentation and report)
-- ═══════════════════════════════════════════════════════════════════

-- Q1: Full-text product search by keyword
-- SELECT * FROM product
-- WHERE status = 'active'
--   AND (name ILIKE '%shoes%' OR description ILIKE '%shoes%');

-- Q2: Filter products by category and price range
-- SELECT p.*, ROUND(p.price * (1 - p.discount_pct/100), 2) AS discounted_price
-- FROM product p
-- JOIN category c ON p.category_id = c.id
-- WHERE c.slug = 'electronics'
--   AND p.price BETWEEN 500 AND 5000
--   AND p.status = 'active'
-- ORDER BY discounted_price ASC;

-- Q3: Average rating per product
-- SELECT p.id, p.name,
--        ROUND(AVG(r.rating), 1) AS avg_rating,
--        COUNT(r.id)             AS review_count
-- FROM product p
-- LEFT JOIN review r ON r.product_id = p.id
-- GROUP BY p.id, p.name
-- ORDER BY avg_rating DESC NULLS LAST;

-- Q4: Customer order history with payment status
-- SELECT o.order_number, o.total_amount, o.status AS order_status,
--        py.method, py.status AS payment_status, o.created_at
-- FROM "order" o
-- JOIN payment py ON py.order_id = o.id
-- WHERE o.customer_id = 1
-- ORDER BY o.created_at DESC;

-- Q5: Vendor revenue report
-- SELECT vp.store_name,
--        COUNT(DISTINCT oi.order_id)        AS total_orders,
--        SUM(oi.line_total)                 AS total_revenue,
--        COUNT(oi.id)                       AS items_sold
-- FROM vendor_profile vp
-- JOIN order_item oi ON oi.vendor_id = vp.id
-- JOIN "order" o ON o.id = oi.order_id
-- WHERE o.status NOT IN ('cancelled','refunded')
-- GROUP BY vp.id, vp.store_name
-- ORDER BY total_revenue DESC;

-- Q6: Low stock alert (stock < 5)
-- SELECT p.name, p.stock, vp.store_name
-- FROM product p
-- JOIN vendor_profile vp ON vp.id = p.vendor_id
-- WHERE p.stock < 5 AND p.status = 'active'
-- ORDER BY p.stock ASC;

-- Q7: Top selling products
-- SELECT p.name, SUM(oi.quantity) AS units_sold, SUM(oi.line_total) AS revenue
-- FROM order_item oi
-- JOIN product p ON p.id = oi.product_id
-- JOIN "order" o ON o.id = oi.order_id
-- WHERE o.status NOT IN ('cancelled','refunded')
-- GROUP BY p.id, p.name
-- ORDER BY units_sold DESC
-- LIMIT 10;

-- Q8: Admin — pending vendor approvals
-- SELECT vp.store_name, up.phone,
--        u.username, u.email, up.created_at
-- FROM vendor_profile vp
-- JOIN user_profile up ON up.id = vp.user_profile_id
-- JOIN auth_user u     ON u.id  = up.user_id
-- WHERE vp.status = 'pending'
-- ORDER BY up.created_at ASC;

-- Q9: Cart total for a user
-- SELECT ci.quantity,
--        p.name,
--        ROUND(p.price * (1 - p.discount_pct/100), 2) AS unit_price,
--        ci.quantity * ROUND(p.price * (1 - p.discount_pct/100), 2) AS line_total
-- FROM cart_item ci
-- JOIN cart c    ON c.id  = ci.cart_id
-- JOIN product p ON p.id  = ci.product_id
-- WHERE c.user_id = 1;

-- Q10: Monthly order revenue
-- SELECT DATE_TRUNC('month', created_at) AS month,
--        COUNT(*)                          AS orders,
--        SUM(total_amount)                AS revenue
-- FROM "order"
-- WHERE status NOT IN ('cancelled','refunded')
-- GROUP BY month
-- ORDER BY month DESC;
