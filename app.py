import os, uuid, random
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash, abort)
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ecommerce-secret-key-2024-change-in-prod')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# ─── DATABASE CONFIGURATION (Supports Local & Cloud) ──────────────────────────
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '12345678'),  
    'database': os.environ.get('DB_NAME', 'ai_ecommerce'), 
    'charset': 'utf8mb4',
    'autocommit': True
}

def get_db():
    try:
        if os.environ.get('DB_HOST'):
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset'],
            autocommit=DB_CONFIG['autocommit']
        )
        
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS ai_ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.close()
        
        conn.database = 'ai_ecommerce'
        return conn
        
    except mysql.connector.Error as err:
        if err.errno == 1045 and DB_CONFIG['password'] == 'root' and not os.environ.get('DB_HOST'):
            print("Password 'root' failed, trying empty password...")
            DB_CONFIG['password'] = ''
            return get_db()
        else:
            raise err

def query(sql, params=None, fetchone=False, fetchall=False):
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetchone:  return cur.fetchone()
        if fetchall:  return cur.fetchall()
        return None
    finally:
        conn.close()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def sanitize(text):
    if not isinstance(text, str): return text
    return text.replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def get_product_full(pid):
    p = query("SELECT * FROM products WHERE id = %s", (pid,), fetchone=True)
    if not p: return None
    p['tags']    = [r['tag'] for r in query("SELECT tag FROM product_tags WHERE product_id = %s", (pid,), fetchall=True)]
    p['reviews'] = query(
        "SELECT user_name AS user, rating, comment, review_date AS date FROM product_reviews WHERE product_id = %s ORDER BY created_at DESC",
        (pid,), fetchall=True
    )
    return p

def get_all_products():
    products = query("SELECT * FROM products", fetchall=True)
    for p in products:
        p['tags'] = [r['tag'] for r in query("SELECT tag FROM product_tags WHERE product_id = %s", (p['id'],), fetchall=True)]
    return products

# ─── Seed Data (Each Category Has Minimum 8 Products With Images) ─────────────
def seed_data():
    defaults = [
        {'id':'admin1',    'email':'admin@ecommerce.com',    'password':'Admin@123',    'role':'admin',    'name':'Admin User'},
        {'id':'seller1',   'email':'seller@ecommerce.com',   'password':'Seller@123',   'role':'seller',   'name':'Tech Store Pro'},
        {'id':'customer1', 'email':'customer@ecommerce.com', 'password':'Customer@123', 'role':'customer', 'name':'Demo Customer'},
    ]
    for d in defaults:
        existing = query("SELECT id FROM users WHERE email = %s", (d['email'],), fetchone=True)
        if not existing:
            query(
                "INSERT INTO users (id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (d['id'], d['name'], d['email'], generate_password_hash(d['password']), d['role'])
            )

    product_count = query("SELECT COUNT(*) AS cnt FROM products", fetchone=True)
    if not product_count or product_count['cnt'] < 5:
        print("Product catalog is empty or low. Seeding 40 default products (8 per category)...")
        
        query("SET FOREIGN_KEY_CHECKS = 0")
        query("TRUNCATE TABLE product_tags")
        query("TRUNCATE TABLE products")
        query("SET FOREIGN_KEY_CHECKS = 1")

        default_products = [
            # 🏪 ELECTRONICS (8 Products)
            {'id': 'elec-1', 'name': 'Wireless Noise-Canceling Headphones', 'category': 'Electronics', 'price': 2499.00, 'original_price': 4999.00, 'description': 'Premium over-ear headphones with deep bass and 30-hour battery life.', 'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500', 'stock': 15, 'brand': 'AudioMax'},
            {'id': 'elec-2', 'name': 'Smart Fitness Watch Series 5', 'category': 'Electronics', 'price': 3499.00, 'original_price': 6999.00, 'description': 'Waterproof fitness tracker with heart rate monitor and AMOLED display.', 'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500', 'stock': 20, 'brand': 'FitTrack'},
            {'id': 'elec-3', 'name': 'Mechanical RGB Gaming Keyboard', 'category': 'Electronics', 'price': 1999.00, 'original_price': 3999.00, 'description': 'Tactile blue switches with customizable RGB backlighting for pro gamers.', 'image': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500', 'stock': 12, 'brand': 'KeyClick'},
            {'id': 'elec-4', 'name': 'Wireless Ergonomic Gaming Mouse', 'category': 'Electronics', 'price': 899.00, 'original_price': 1799.00, 'description': 'High DPI optical sensor with ultra-lightweight design and long battery life.', 'image': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500', 'stock': 25, 'brand': 'LogiTech'},
            {'id': 'elec-5', 'name': 'Portable Waterproof Bluetooth Speaker', 'category': 'Electronics', 'price': 1299.00, 'original_price': 2499.00, 'description': 'Powerful 360-degree sound with rich bass, perfect for outdoor parties.', 'image': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500', 'stock': 30, 'brand': 'SoundBoom'},
            {'id': 'elec-6', 'name': '4K Ultra HD Action Camera', 'category': 'Electronics', 'price': 4599.00, 'original_price': 8999.00, 'description': 'Capture your adventures in stunning 4K with image stabilization.', 'image': 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500', 'stock': 8, 'brand': 'GoCam'},
            {'id': 'elec-7', 'name': 'Fast Wireless Charging Pad', 'category': 'Electronics', 'price': 699.00, 'original_price': 1299.00, 'description': '15W fast charging dock compatible with all Qi-enabled smartphones.', 'image': 'https://images.unsplash.com/photo-1622445262465-2481c4574875?w=500', 'stock': 50, 'brand': 'ChargeUp'},
            {'id': 'elec-8', 'name': 'True Wireless Earbuds with ANC', 'category': 'Electronics', 'price': 1799.00, 'original_price': 3499.00, 'description': 'Compact style earbuds with touch controls and clear voice calls.', 'image': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500', 'stock': 40, 'brand': 'AirSonic'},

            # 👕 FASHION (8 Products)
            {'id': 'fash-1', 'name': 'Classic Denim Trucker Jacket', 'category': 'Fashion', 'price': 1899.00, 'original_price': 2999.00, 'description': 'Timeless blue denim jacket crafted from durable premium cotton.', 'image': 'https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=500', 'stock': 18, 'brand': 'DenimCo'},
            {'id': 'fash-2', 'name': 'Minimalist Genuine Leather Wallet', 'category': 'Fashion', 'price': 799.00, 'original_price': 1499.00, 'description': 'Slim bifold leather wallet featuring advanced RFID block security.', 'image': 'https://images.unsplash.com/photo-1627123424574-724758594e93?w=500', 'stock': 35, 'brand': 'HideCraft'},
            {'id': 'fash-3', 'name': 'Unisex Urban Canvas Backpack', 'category': 'Fashion', 'price': 1199.00, 'original_price': 1999.00, 'description': 'Spacious everyday vintage backpack with dedicated 15.6 inch laptop sleeve.', 'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500', 'stock': 22, 'brand': 'PackGear'},
            {'id': 'fash-4', 'name': 'Breathable Mesh Running Sneakers', 'category': 'Fashion', 'price': 2199.00, 'original_price': 3999.00, 'description': 'Lightweight active sports shoes with responsive cushioning.', 'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500', 'stock': 14, 'brand': 'AeroPace'},
            {'id': 'fash-5', 'name': 'Polarized Retro Sunglasses', 'category': 'Fashion', 'price': 599.00, 'original_price': 999.00, 'description': 'Classic matte black square sunglasses with UV400 protection.', 'image': 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500', 'stock': 50, 'brand': 'SunRay'},
            {'id': 'fash-6', 'name': 'Premium Chronograph Wristwatch', 'category': 'Fashion', 'price': 2999.00, 'original_price': 5999.00, 'description': 'Elegant analog stainless steel luxury watch for business or casual attire.', 'image': 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=500', 'stock': 10, 'brand': 'TimeMaster'},
            {'id': 'fash-7', 'name': 'Pure Cotton Casual Slim Fit Shirt', 'category': 'Fashion', 'price': 899.00, 'original_price': 1599.00, 'description': 'Breathable solid color button-down plain casual shirt.', 'image': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500', 'stock': 28, 'brand': 'VogueFit'},
            {'id': 'fash-8', 'name': 'Cozy Oversized Fleece Hoodie', 'category': 'Fashion', 'price': 1499.00, 'original_price': 2499.00, 'description': 'Super-soft heavy brushed cotton winter hoodie with front pouch.', 'image': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500', 'stock': 16, 'brand': 'ComfyWear'},

            # 📚 BOOKS (8 Products)
            {'id': 'book-1', 'name': 'Python Programming Mastery Blueprint', 'category': 'Books', 'price': 599.00, 'original_price': 999.00, 'description': 'Complete structural reference guide from beginner syntax to production architecture.', 'image': 'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=500', 'stock': 60, 'brand': 'TechPress'},
            {'id': 'book-2', 'name': 'The Art of Deep Minimalist Graphic Design', 'category': 'Books', 'price': 799.00, 'original_price': 1299.00, 'description': 'Learn standard grids, color psychology, and sleek modern branding principles.', 'image': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500', 'stock': 30, 'brand': 'CreativeEd'},
            {'id': 'book-3', 'name': 'Atomic Habits & Daily Routines', 'category': 'Books', 'price': 399.00, 'original_price': 599.00, 'description': 'Legendary self-improvement guide to building positive systems and crushing goals.', 'image': 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=500', 'stock': 45, 'brand': 'MindPower'},
            {'id': 'book-4', 'name': 'Data Structures & Algorithms in Java', 'category': 'Books', 'price': 699.00, 'original_price': 1199.00, 'description': 'Comprehensive roadmap for technical interview preparation at top tech firms.', 'image': 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500', 'stock': 25, 'brand': 'CodeBooks'},
            {'id': 'book-5', 'name': 'The Futuristic AI Revolution Chronicles', 'category': 'Books', 'price': 499.00, 'original_price': 799.00, 'description': 'A deep speculative dive into deep learning, neural networks, and human legacy.', 'image': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500', 'stock': 35, 'brand': 'SciFiPub'},
            {'id': 'book-6', 'name': 'Gordon Cooking Masterclass Essentials', 'category': 'Books', 'price': 999.00, 'original_price': 1499.00, 'description': 'Professional step-by-step culinary guides and secret restaurant recipes.', 'image': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500', 'stock': 15, 'brand': 'ChefLife'},
            {'id': 'book-7', 'name': 'The Complete Financial Independence Guide', 'category': 'Books', 'price': 449.00, 'original_price': 699.00, 'description': 'Master wealth management, budgeting metrics, and stock market investments.', 'image': 'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=500', 'stock': 40, 'brand': 'WealthInc'},
            {'id': 'book-8', 'name': 'The Mountain Solitude Traveler Diary', 'category': 'Books', 'price': 349.00, 'original_price': 499.00, 'description': 'Beautiful cinematic storytelling of solo wilderness photography journeys.', 'image': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=500', 'stock': 20, 'brand': 'NaturePress'},

            # 🎮 GAMING (8 Products)
            {'id': 'game-1', 'name': 'Next-Gen Wireless Pro Controller', 'category': 'Gaming', 'price': 3999.00, 'original_price': 5999.00, 'description': 'Ergonomic layout with haptic feedback feedback and remappable back paddles.', 'image': 'https://images.unsplash.com/photo-1600861195091-690c92f1d2cc?w=500', 'stock': 14, 'brand': 'PlayGear'},
            {'id': 'game-2', 'name': '7.1 Surround Sound Gaming Headset', 'category': 'Gaming', 'price': 2799.00, 'original_price': 4999.00, 'description': 'Ultra-comfortable memory foam cups with noise-canceling detachable mic.', 'image': 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500', 'stock': 18, 'brand': 'RazerX'},
            {'id': 'game-3', 'name': 'RGB Extra Large Desk Mousepad', 'category': 'Gaming', 'price': 699.00, 'original_price': 1299.00, 'description': 'Smooth micro-textured cloth surface with stitched glowing LED edges.', 'image': 'https://images.unsplash.com/photo-1616440347437-b1c73416efc2?w=500', 'stock': 40, 'brand': 'GlowDesk'},
            {'id': 'game-4', 'name': 'Dual Controller Charging Dock Station', 'category': 'Gaming', 'price': 1199.00, 'original_price': 1999.00, 'description': 'Fast click-in charging base layout for wireless gamepads.', 'image': 'https://images.unsplash.com/photo-1592155931584-901ac15763e3?w=500', 'stock': 25, 'brand': 'ChargeStation'},
            {'id': 'game-5', 'name': 'Retro Handheld Console (4000+ Games)', 'category': 'Gaming', 'price': 2499.00, 'original_price': 3999.00, 'description': 'IPS crisp display packed with nostalgic 8-bit and 16-bit arcade games.', 'image': 'https://images.unsplash.com/photo-1531525645387-7f14be1bdbbd?w=500', 'stock': 15, 'brand': 'RetroPlay'},
            {'id': 'game-6', 'name': 'Streaming HD USB Condenser Microphone', 'category': 'Gaming', 'price': 3199.00, 'original_price': 5999.00, 'description': 'Cardioid pattern audio capture unit with pop filter for live streaming.', 'image': 'https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=500', 'stock': 12, 'brand': 'VocalPro'},
            {'id': 'game-7', 'name': 'Full Aluminum Flight Simulation Joystick', 'category': 'Gaming', 'price': 5499.00, 'original_price': 9999.00, 'description': 'Precision throttle quadrants mapping responsive space flight axes.', 'image': 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=500', 'stock': 6, 'brand': 'AeroFly'},
            {'id': 'game-8', 'name': 'Customizable Game Case Organizer Rack', 'category': 'Gaming', 'price': 899.00, 'original_price': 1499.00, 'description': 'Vertical storage mount fitting up to 12 discs or switch cartridge cases.', 'image': 'https://images.unsplash.com/photo-1585620385456-4759f9b5c7d9?w=500', 'stock': 30, 'brand': 'VaultCase'},

            # ⚽ SPORTS (8 Products)
            {'id': 'spor-1', 'name': 'Premium Leather English Soccer Ball', 'category': 'Sports', 'price': 999.00, 'original_price': 1799.00, 'description': 'Official size 5 matching match ball with high air-retention bladder.', 'image': 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500', 'stock': 20, 'brand': 'GoalKick'},
            {'id': 'spor-2', 'name': 'Anti-Slip High Density Yoga Mat', 'category': 'Sports', 'price': 849.00, 'original_price': 1599.00, 'description': '6mm thick eco-friendly cushion padding carrying strap included.', 'image': 'https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=500', 'stock': 35, 'brand': 'ZenCushion'},
            {'id': 'spor-3', 'name': 'Adjustable Steel Dumbbell Set (20KG)', 'category': 'Sports', 'price': 2999.00, 'original_price': 4999.00, 'description': 'Solid metal chrome plates with tight star-lock collars for strength lifts.', 'image': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=500', 'stock': 10, 'brand': 'IronGrip'},
            {'id': 'spor-4', 'name': 'Insulated Stainless Steel Sports Bottle', 'category': 'Sports', 'price': 649.00, 'original_price': 1199.00, 'description': 'Double-walled vacuum flask keeping liquids ice cold for 24 hours.', 'image': 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500', 'stock': 50, 'brand': 'HydroFlask'},
            {'id': 'spor-5', 'name': 'Carbon Fiber Heavy Spin Badminton Racket', 'category': 'Sports', 'price': 1499.00, 'original_price': 2699.00, 'description': 'Ultra-light high tension frame strings delivering swift smashes.', 'image': 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=500', 'stock': 16, 'brand': 'FlySmash'},
            {'id': 'spor-6', 'name': 'Heavy Duty Core Exercise Resistance Bands', 'category': 'Sports', 'price': 499.00, 'original_price': 899.00, 'description': '5 varying elasticity fitness loops for workout target progression.', 'image': 'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=500', 'stock': 45, 'brand': 'FlexLoop'},
            {'id': 'spor-7', 'name': 'Professional Waterproof Swimming Goggles', 'category': 'Sports', 'price': 549.00, 'original_price': 999.00, 'description': 'Anti-fog wide view lenses with soft leak-proof silicone seals.', 'image': 'https://images.unsplash.com/photo-1582971805810-b24306e0afe5?w=500', 'stock': 25, 'brand': 'AquaShield'},
            {'id': 'spor-8', 'name': 'Heavy-Duty Boxing Punching Gloves', 'category': 'Sports', 'price': 1799.00, 'original_price': 2999.00, 'description': 'Multi-layered gel foam shock protection wrist secure strap boxing gear.', 'image': 'https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?w=500', 'stock': 12, 'brand': 'StrikeForce'}
        ]
        
        for p in default_products:
            query("""
                INSERT INTO products (id, name, category, price, original_price, description, image,
                    reviews_count, stock, seller_id, seller_name, brand, rating, featured, trending, best_seller)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, 'seller1', 'Tech Store Pro', %s, 4.5, 1, 1, 1)
            """, (p['id'], p['name'], p['category'], p['price'], p['original_price'], p['description'], p['image'], p['stock'], p['brand']))
            
            query("INSERT INTO product_tags (product_id, tag) VALUES (%s, %s)", (p['id'], p['category'].lower()))
        print("40 Default products successfully seeded inside the remote database!")

# ─── Auth Decorators ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.','warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in.','warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles: abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── Recommendations ──────────────────────────────────────────────────────────
def get_recommendations(user_id, exclude_id=None, limit=6):
    products = get_all_products()
    history  = [r['product_id'] for r in query(
        "SELECT product_id FROM browsing_history WHERE user_id = %s ORDER BY viewed_at DESC LIMIT 20",
        (user_id,), fetchall=True
    )]
    cat_count = {}
    for pid in history:
        p = next((x for x in products if x['id'] == pid), None)
        if p: cat_count[p['category']] = cat_count.get(p['category'], 0) + 1
    recent5 = set(history[:5])
    scored  = []
    for p in products:
        if p['id'] == exclude_id or p['id'] in recent5: continue
        score = cat_count.get(p['category'], 0) * 2 + float(p['rating'])
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]

def track_view(user_id, product_id):
    query("DELETE FROM browsing_history WHERE user_id = %s AND product_id = %s", (user_id, product_id))
    query("INSERT INTO browsing_history (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
    query("""
        DELETE FROM browsing_history WHERE user_id = %s AND id NOT IN (
            SELECT id FROM (
                SELECT id FROM browsing_history WHERE user_id = %s ORDER BY viewed_at DESC LIMIT 50
            ) t
        )
    """, (user_id, user_id))

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect(url_for('home'))
    if request.method == 'POST':
        email    = sanitize(request.form.get('email','').strip().lower())
        password = request.form.get('password','')
        user = query("SELECT * FROM users WHERE email = %s", (email,), fetchone=True)
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['role']    = user['role']
            session['name']    = user['name']
            session['email']   = user['email']
            flash(f'Welcome back, {user["name"]}!', 'success')
            nxt = request.args.get('next')
            if nxt: return redirect(nxt)
            if user['role'] == 'admin':  return redirect(url_for('admin_dashboard'))
            if user['role'] == 'seller': return redirect(url_for('seller_dashboard'))
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if 'user_id' in session: return redirect(url_for('home'))
    if request.method == 'POST':
        name     = sanitize(request.form.get('name','').strip())
        email    = sanitize(request.form.get('email','').strip().lower())
        password = request.form.get('password','')
        phone    = sanitize(request.form.get('phone','').strip())
        role     = request.form.get('role','customer')
        if role not in ('customer','seller'): role = 'customer'
        if not name or not email or not password:
            flash('All fields are required.','danger')
            return render_template('register.html')
        if query("SELECT id FROM users WHERE email = %s", (email,), fetchone=True):
            flash('Email already registered.','danger')
            return render_template('register.html')
        uid = str(uuid.uuid4())
        query("INSERT INTO users (id, name, email, password, phone, role) VALUES (%s,%s,%s,%s,%s,%s)",
              (uid, name, email, generate_password_hash(password), phone, role))
        flash('Account created! Please log in.','success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.','info')
    return redirect(url_for('login'))

@app.route('/')
def home():
    products   = get_all_products()
    featured   = [p for p in products if p.get('featured')][:8]
    trending   = [p for p in products if p.get('trending')][:8]
    best       = [p for p in products if p.get('best_seller')][:8]
    categories = list({p['category'] for p in products})
    recs = get_recommendations(session['user_id'], limit=6) if 'user_id' in session else []
    return render_template('home.html', featured=featured, trending=trending,
        best_sellers=best, categories=categories, recommendations=recs, products=products)

@app.route('/products')
def products_page():
    q        = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip()
    min_p    = request.args.get('min_price', type=float)
    max_p    = request.args.get('max_price', type=float)
    sort     = request.args.get('sort', '')
    
    sql, params = "SELECT * FROM products WHERE 1=1", []
    
    if category:
        sql += " AND category = %s"
        params.append(category)
        
    if q:
        words = q.split()
        for word in words:
            sql += " AND (LOWER(name) LIKE %s OR LOWER(description) LIKE %s OR LOWER(category) LIKE %s OR LOWER(brand) LIKE %s)"
            like_param = f'%{word}%'
            params += [like_param, like_param, like_param, like_param]

    if min_p is not None:
        sql += " AND price >= %s"; params.append(min_p)
    if max_p is not None:
        sql += " AND price <= %s"; params.append(max_p)
        
    if sort == 'price_asc':    sql += " ORDER BY price ASC"
    elif sort == 'price_desc': sql += " ORDER BY price DESC"
    elif sort == 'rating':     sql += " ORDER BY rating DESC"
    
    filtered   = query(sql, params, fetchall=True)
    categories = [r['category'] for r in query("SELECT DISTINCT category FROM products", fetchall=True)]
    
    return render_template('products.html', products=filtered, categories=categories,
        query=request.args.get('q', ''), selected_category=category, sort=sort)

@app.route('/product/<pid>')
def product_detail(pid):
    product = get_product_full(pid)
    if not product: abort(404)
    if 'user_id' in session:
        track_view(session['user_id'], pid)
        recs = get_recommendations(session['user_id'], exclude_id=pid, limit=6)
    else:
        all_prods = get_all_products()
        recs = random.sample([p for p in all_prods if p['id'] != pid], min(6, len(all_prods)-1))
    related = query("SELECT * FROM products WHERE category = %s AND id != %s LIMIT 4",
                    (product['category'], pid), fetchall=True)
    in_wishlist = bool(query("SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s",
                             (session.get('user_id',''), pid), fetchone=True)) if 'user_id' in session else False
    return render_template('product_detail.html', product=product,
        recommendations=recs, related=related, in_wishlist=in_wishlist)

@app.route('/cart')
@login_required
def cart():
    rows  = query("""
        SELECT p.*, c.quantity, (p.price * c.quantity) AS subtotal
        FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = %s
    """, (session['user_id'],), fetchall=True)
    total = sum(float(r['subtotal']) for r in rows)
    return render_template('cart.html', items=rows, total=total)

@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    pid = request.form.get('product_id')
    qty = int(request.form.get('quantity', 1))
    query("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE quantity = quantity + %s",
          (session['user_id'], pid, qty, qty))
    flash('Added to cart!', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    query("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
          (max(1, int(request.form.get('quantity', 1))), session['user_id'], request.form.get('product_id')))
    return redirect(url_for('cart'))

@app.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    query("DELETE FROM cart WHERE user_id = %s AND product_id = %s",
          (session['user_id'], request.form.get('product_id')))
    flash('Removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/wishlist')
@login_required
def wishlist():
    items = query("""
        SELECT p.* FROM wishlist w JOIN products p ON w.product_id = p.id WHERE w.user_id = %s
    """, (session['user_id'],), fetchall=True)
    return render_template('wishlist.html', items=items)

@app.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    pid, uid = request.form.get('product_id'), session['user_id']
    if query("SELECT id FROM wishlist WHERE user_id = %s AND product_id = %s", (uid, pid), fetchone=True):
        query("DELETE FROM wishlist WHERE user_id = %s AND product_id = %s", (uid, pid))
        flash('Removed from wishlist.', 'info')
    else:
        query("INSERT INTO wishlist (user_id, product_id) VALUES (%s,%s)", (uid, pid))
        flash('Added to wishlist!', 'success')
    return redirect(request.referrer or url_for('wishlist'))

@app.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    uid  = session['user_id']
    user  = query("SELECT * FROM users WHERE id = %s", (uid,), fetchone=True)
    
    is_buy_now = request.args.get('buy_now') == 'true'
    buy_now_pid = request.args.get('product_id')
    buy_now_qty = request.args.get('quantity', 1, type=int)

    if is_buy_now and buy_now_pid:
        p = query("SELECT * FROM products WHERE id = %s", (buy_now_pid,), fetchone=True)
        if not p:
            flash('Product profile entry target not found.', 'danger')
            return redirect(url_for('home'))
        p['quantity'] = buy_now_qty
        p['subtotal'] = float(p['price']) * buy_now_qty
        rows = [p]
    else:
        rows = query("""
            SELECT p.*, c.quantity, (p.price * c.quantity) AS subtotal
            FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = %s
        """, (uid,), fetchall=True)

    if not rows:
        flash('Your cart is empty.','warning')
        return redirect(url_for('cart'))
        
    total = sum(float(r['subtotal']) for r in rows)
    
    if request.method == 'POST':
        oid = 'ORD-' + str(uuid.uuid4())[:8].upper()
        query("""
            INSERT INTO orders (id, user_id, user_name, phone, address, city, state, pincode, total)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (oid, uid,
              sanitize(request.form.get('full_name','')), sanitize(request.form.get('phone','')),
              sanitize(request.form.get('address','')),   sanitize(request.form.get('city','')),
              sanitize(request.form.get('state','')),     sanitize(request.form.get('pincode','')), total))
              
        for item in rows:
            query("INSERT INTO order_items (order_id, product_id, name, price, quantity, subtotal) VALUES (%s,%s,%s,%s,%s,%s)",
                  (oid, item['id'], item['name'], item['price'], item['quantity'], item['subtotal']))
                  
        if not is_buy_now:
            query("DELETE FROM cart WHERE user_id = %s", (uid,))
            
        flash(f'Order placed! Your Order ID is {oid}', 'success')
        return redirect(url_for('order_success', order_id=oid))
    return render_template('checkout.html', items=rows, total=total, user=user)

@app.route('/order/success/<order_id>')
@login_required
def order_success(order_id):
    order = query("SELECT * FROM orders WHERE id = %s AND user_id = %s",
                  (order_id, session['user_id']), fetchone=True)
    if not order: abort(404)
    
    if order.get('created_at') and isinstance(order['created_at'], datetime):
        order['created_at'] = order['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
    order['items'] = query("SELECT * FROM order_items WHERE order_id = %s", (order_id,), fetchall=True)
    return render_template('order_success.html', order=order)

@app.route('/orders')
@login_required
def orders():
    all_orders = query("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC",
                       (session['user_id'],), fetchall=True)
    for o in all_orders:
        if o.get('created_at') and isinstance(o['created_at'], datetime):
            o['created_at'] = o['created_at'].strftime('%Y-%m-%d')
            
        o['items'] = query("SELECT * FROM order_items WHERE order_id = %s", (o['id'],), fetchall=True)
    return render_template('orders.html', orders=all_orders)

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    uid  = session['user_id']
    user = query("SELECT * FROM users WHERE id = %s", (uid,), fetchone=True)
    if request.method == 'POST':
        name = sanitize(request.form.get('name', user['name']))
        query("UPDATE users SET name=%s,phone=%s,address=%s,city=%s,state=%s,pincode=%s WHERE id=%s",
              (name, sanitize(request.form.get('phone','')), sanitize(request.form.get('address','')),
               sanitize(request.form.get('city','')), sanitize(request.form.get('state','')),
               sanitize(request.form.get('pincode','')), uid))
        session['name'] = name
        flash('Profile updated!','success')
        user = query("SELECT * FROM users WHERE id = %s", (uid,), fetchone=True)
    user_orders = query("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC", (uid,), fetchall=True)
    
    for o in user_orders:
        if o.get('created_at') and isinstance(o['created_at'], datetime):
            o['created_at'] = o['created_at'].strftime('%Y-%m-%d')
            
    return render_template('profile.html', user=user, orders=user_orders)

@app.route('/seller')
@role_required('seller')
def seller_dashboard():
    sid      = session['user_id']
    my_prods = query("SELECT * FROM products WHERE seller_id = %s", (sid,), fetchall=True)
    my_pids  = [p['id'] for p in my_prods]
    my_orders, total_earnings = [], 0
    monthly = {} 
    
    if my_pids:
        placeholders = ','.join(['%s'] * len(my_pids))
        items = query(f"""
            SELECT oi.*, o.created_at AS order_date, o.id AS oid
            FROM order_items oi JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id IN ({placeholders})
        """, my_pids, fetchall=True)
        seen = set()
        for item in items:
            total_earnings += float(item['subtotal'])
            month = str(item['order_date'])[:7]
            monthly[month] = monthly.get(month, 0) + float(item['subtotal'])
            if item['oid'] not in seen:
                o = query("SELECT * FROM orders WHERE id = %s", (item['oid'],), fetchone=True)
                if o: my_orders.append(o)
                seen.add(item['oid'])
    return render_template('seller_dashboard.html', products=my_prods,
        orders=my_orders, total_earnings=total_earnings, monthly_earnings=monthly)

@app.route('/seller/product/add', methods=['GET','POST'])
@role_required('seller')
def seller_add_product():
    if request.method == 'POST':
        pid = 'p' + str(uuid.uuid4())[:8]
        name = sanitize(request.form.get('name', ''))
        category = sanitize(request.form.get('category', ''))
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price', 0))
        description = sanitize(request.form.get('description', ''))
        image = sanitize(request.form.get('image', ''))
        stock = int(request.form.get('stock', 0))
        brand = sanitize(request.form.get('brand', ''))
        
        query("""
            INSERT INTO products (id,name,category,price,original_price,description,image,
                reviews_count,stock,seller_id,seller_name,brand,rating,featured,trending,best_seller)
            VALUES (%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s,4.0,0,0,0)
        """, (pid, name, category, price, original_price, description, image,
              stock, session['user_id'], session['name'], brand))
        flash('Product successfully published onto the catalog network!', 'success')
        return redirect(url_for('seller_dashboard'))
    return render_template('seller_add_product.html')

@app.route('/seller/product/edit/<pid>', methods=['GET','POST'])
@role_required('seller')
def seller_edit_product(pid):
    product = query("SELECT * FROM products WHERE id=%s AND seller_id=%s", (pid, session['user_id']), fetchone=True)
    if not product: abort(404)
    if request.method == 'POST':
        name = sanitize(request.form.get('name', ''))
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price', 0))
        description = sanitize(request.form.get('description', ''))
        image = sanitize(request.form.get('image', ''))
        stock = int(request.form.get('stock', 0))
        brand = sanitize(request.form.get('brand', ''))
        
        query("""
            UPDATE products 
            SET name=%s,price=%s,original_price=%s,description=%s,image=%s,stock=%s,brand=%s 
            WHERE id=%s AND seller_id=%s
        """, (name, price, original_price, description, image, stock, brand, pid, session['user_id']))
        flash('Product catalog details synchronized successfully!', 'success')
        return redirect(url_for('seller_dashboard'))
    return render_template('seller_edit_product.html', product=product)

@app.route('/seller/product/delete/<pid>', methods=['POST'])
@role_required('seller')
def seller_delete_product(pid):
    query("DELETE FROM products WHERE id=%s AND seller_id=%s", (pid, session['user_id']))
    flash('Product deleted.','info')
    return redirect(url_for('seller_dashboard'))

@app.route('/admin')
@role_required('admin')
def admin_dashboard():
    users    = query("SELECT * FROM users", fetchall=True)
    products = query("SELECT * FROM products", fetchall=True)
    orders   = query("SELECT * FROM orders", fetchall=True)
    return render_template('admin_dashboard.html', users=users, products=products, orders=orders,
        total_revenue=sum(float(o['total']) for o in orders),
        sellers=[u for u in users if u['role']=='seller'],
        customers=[u for u in users if u['role']=='customer'])

@app.route('/admin/user/delete/<uid>', methods=['POST'])
@role_required('admin')
def admin_delete_user(uid):
    if uid == session['user_id']:
        flash("Can't delete yourself.",'danger')
        return redirect(url_for('admin_dashboard'))
    query("DELETE FROM users WHERE id=%s", (uid,))
    flash('User deleted.','info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/delete/<pid>', methods=['POST'])
@role_required('admin')
def admin_delete_product(pid):
    query("DELETE FROM products WHERE id=%s", (pid,))
    flash('Product deleted.','info')
    return redirect(url_for('admin_dashboard'))

@app.route('/product/<pid>/review', methods=['POST'])
@login_required
def add_review(pid):
    rating  = int(request.form.get('rating', 5))
    comment = sanitize(request.form.get('comment',''))
    if not comment:
        flash('Comment cannot be empty.','danger')
        return redirect(url_for('product_detail', pid=pid))
    query("INSERT INTO product_reviews (product_id, user_name, rating, comment, review_date) VALUES (%s,%s,%s,%s,%s)",
          (pid, session['name'], rating, comment, datetime.now().date()))
    result = query("SELECT AVG(rating) AS avg_r, COUNT(*) AS cnt FROM product_reviews WHERE product_id=%s", (pid,), fetchone=True)
    query("UPDATE products SET rating=%s, reviews_count=%s WHERE id=%s",
          (round(float(result['avg_r']), 1), result['cnt'], pid))
    flash('Review submitted!','success')
    return redirect(url_for('product_detail', pid=pid))

@app.route('/api/search')
def api_search():
    results = query("SELECT id, name, price, image FROM products WHERE LOWER(name) LIKE %s LIMIT 5",
                    (f'%{request.args.get("q","").lower()}%',), fetchall=True)
    return jsonify(results)

@app.errorhandler(403)
def forbidden(e):    return render_template('error.html', code=403, msg='Access Denied'), 403
@app.errorhandler(404)
def not_found(e):    return render_template('error.html', code=404, msg='Page Not Found'), 404
@app.errorhandler(500)
def server_error(e): return render_template('error.html', code=500, msg='Internal Server Error'), 500

# ─── Custom Template Filters Layer ───
@app.template_filter('rupee')
def rupee_filter(value):
    try:
        if value is None: return "₹0"
        return f'₹{int(value):,}'
    except (ValueError, TypeError):
        return f'₹{value}'

@app.template_filter('stars')
def stars_filter(rating):
    try:
        full = int(rating); half = 1 if (float(rating)-full) >= 0.5 else 0
        return '★'*full + '½'*half + '☆'*(5-full-half)
    except (ValueError, TypeError):
        return '☆☆☆☆☆'

@app.context_processor
def inject_globals():
    cart_count = 0
    if 'user_id' in session:
        result = query("SELECT SUM(quantity) AS total FROM cart WHERE user_id=%s", (session['user_id'],), fetchone=True)
        cart_count = int(result['total']) if result and result['total'] else 0
    return dict(cart_count=cart_count)

if __name__ == '__main__':
    try:
        if os.path.exists('schema.sql') and not os.environ.get('DB_HOST'):
            print("Loading schema.sql to initialize tables locally...")
            db_conn = get_db()
            db_cur = db_conn.cursor()
            
            with open('schema.sql', 'r', encoding='utf-8') as f:
                sql_commands = f.read().split(';')
                for command in sql_commands:
                    if command.strip():
                        db_cur.execute(command)
            
            db_conn.commit()
            db_cur.close()
            db_conn.close()
            print("Tables initialized successfully!")
    except Exception as e:
        print(f"Schema loading note: {e}")

    try:
        seed_data()
    except Exception as e:
        print(f"Initial seeding note: {e}")
        
    app.run(debug=True, port=5005)
