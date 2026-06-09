

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



DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',  
    'charset': 'utf8mb4',
    'autocommit': True
}

def get_db():
    try:
       
        conn = mysql.connector.connect(**DB_CONFIG)
        
       
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS ai_ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.close()
        
      
        conn.database = 'ai_ecommerce'
        return conn
        
    except mysql.connector.Error as err:
        
        if err.errno == 1045 and DB_CONFIG['password'] == 'root':
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

# ─── Seed Data ────────────────────────────────────────────────────────────────
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

# ── Supports Direct Buy Now Link Redirect Handling ──
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

# ── 🏪 Seller Dashboard Route (Fixed Built-in Iteration Empty Dict Crash) ──
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

# ── ➕ Seller Add Product Route (Supports Sync Brand & Original Price Form Maps) ──
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

# ── ✏️ Seller Edit Product Route (Fixed Sync Target Structural Pipeline) ──
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
        if os.path.exists('schema.sql'):
            print("Loading schema.sql to initialize tables...")
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
