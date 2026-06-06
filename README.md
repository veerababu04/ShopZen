



# ShopZen 🛍️

A full-stack e-commerce web app built with Flask and MySQL. Supports three types of users — customers, sellers, and admins — each with their own dashboard and set of features.

---

## What it does

Customers can browse products, add them to a cart or wishlist, and place orders. Sellers can list and manage their own products and track earnings. Admins get a bird's-eye view of everything — users, products, and orders.

There's also a simple recommendation engine that looks at a user's browsing history and suggests products they might like.

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL (via `mysql-connector-python`)
- **Frontend:** Jinja2 templates, HTML/CSS/JS
- **Auth:** Session-based login with hashed passwords (Werkzeug)

---

## Project Structure

```
ShopZen/
├── app.py              # All routes and backend logic
├── schema.sql          # Database schema (run this first)
├── requirements.txt    # Python dependencies
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html
│   ├── products.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── checkout.html
│   ├── orders.html
│   ├── wishlist.html
│   ├── profile.html
│   ├── seller_dashboard.html
│   ├── seller_add_product.html
│   ├── seller_edit_product.html
│   ├── admin_dashboard.html
│   ├── login.html
│   ├── register.html
│   └── error.html
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ShopZen.git
cd ShopZen
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up MySQL

Make sure MySQL is running locally. The app will auto-create the database on first run, but you should initialize the tables from the schema file first:

```bash
mysql -u root -p < schema.sql
```

### 4. Configure your DB password

In `app.py`, update the `DB_CONFIG` block with your MySQL credentials:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password_here',
    ...
}
```

> Don't push your real password to GitHub. Consider moving this to a `.env` file.

### 5. Run the app

```bash
python3 app.py
```

App runs on `http://localhost:5005` by default.

---

## Default Test Accounts

The app seeds these accounts automatically on first run:

| Role     | Email                    | Password      |
|----------|--------------------------|---------------|
| Admin    | admin@ecommerce.com      | Admin@123     |
| Seller   | seller@ecommerce.com     | Seller@123    |
| Customer | customer@ecommerce.com   | Customer@123  |

---

## Features

**For Customers**
- Browse and search products by name, category, or price range
- Product detail pages with reviews and ratings
- Add to cart / wishlist
- "Buy Now" option that skips the cart
- Checkout with delivery details
- View order history
- Personalized product recommendations based on browsing history

**For Sellers**
- Add, edit, and delete your own products
- View orders containing your products
- Track monthly earnings

**For Admins**
- View all users, products, and orders
- Delete users or products

