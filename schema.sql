-- AI E-Commerce MySQL Schema
-- Run this once to set up your database

CREATE DATABASE IF NOT EXISTS ai_ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_ecommerce;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'seller', 'customer') DEFAULT 'customer',
    phone VARCHAR(20) DEFAULT '',
    address TEXT ,
    city VARCHAR(100) DEFAULT '',
    state VARCHAR(100) DEFAULT '',
    pincode VARCHAR(10) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Browsing history (separate table since it's a list per user)
CREATE TABLE IF NOT EXISTS browsing_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    image VARCHAR(500) DEFAULT '',
    rating DECIMAL(3,1) DEFAULT 0,
    reviews_count INT DEFAULT 0,
    stock INT DEFAULT 0,
    seller_id VARCHAR(36),
    seller_name VARCHAR(255) DEFAULT '',
    brand VARCHAR(100) DEFAULT '',
    featured TINYINT(1) DEFAULT 0,
    trending TINYINT(1) DEFAULT 0,
    best_seller TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Product tags
CREATE TABLE IF NOT EXISTS product_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL,
    tag VARCHAR(100) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product reviews
CREATE TABLE IF NOT EXISTS product_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(20) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL,
    review_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(20) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    user_name VARCHAR(255) DEFAULT '',
    phone VARCHAR(20) DEFAULT '',
    address TEXT ,
    city VARCHAR(100) DEFAULT '',
    state VARCHAR(100) DEFAULT '',
    pincode VARCHAR(10) DEFAULT '',
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Confirmed',
    payment VARCHAR(100) DEFAULT 'Cash on Delivery',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Cart table
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_cart_item (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Wishlist table
CREATE TABLE IF NOT EXISTS wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_wishlist_item (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ─── Seed Products (7 per category) ─────────────────────────────────────────
-- seller1 must exist first (created by seed_data() in app.py on first run)
-- Run app.py once, then run this section, OR run full schema fresh.

-- Electronics (7)
INSERT IGNORE INTO products (id,name,category,price,original_price,description,image,rating,reviews_count,stock,seller_id,seller_name,brand,featured,trending,best_seller) VALUES
('p001','iPhone 15 Pro','Electronics',119999,129999,'The iPhone 15 Pro features a titanium design, A17 Pro chip, and a customizable Action button. 48MP main camera with next-gen portraits and 4K video.','https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400&q=80',4.8,2341,50,'seller1','Tech Store Pro','Apple',1,1,1),
('p002','Samsung Galaxy S25','Electronics',94999,99999,'Samsung Galaxy S25 with Snapdragon 8 Elite, 50MP triple camera, 4000mAh battery.','https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400&q=80',4.6,1876,75,'seller1','Tech Store Pro','Samsung',1,1,0),
('p003','MacBook Air M3','Electronics',134999,139999,'MacBook Air with M3 chip, 18 hours battery, up to 60% faster than M1.','https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400&q=80',4.9,987,30,'seller1','Tech Store Pro','Apple',1,0,1),
('p004','Sony WH-1000XM5','Electronics',29999,34999,'Industry-leading noise cancelling headphones, 30-hour battery.','https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400&q=80',4.7,3421,100,'seller1','Tech Store Pro','Sony',0,1,1),
('p005','iPad Pro 12.9 M2','Electronics',109999,119999,'iPad Pro with M2 chip, Liquid Retina XDR display, Apple Pencil support.','https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&q=80',4.8,1543,40,'seller1','Tech Store Pro','Apple',1,1,0),
('p006','Samsung Galaxy Watch 6','Electronics',24999,29999,'Advanced health monitoring, sleep tracking, 40hr battery life.','https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&q=80',4.5,876,60,'seller1','Tech Store Pro','Samsung',0,1,0),
('p007','OnePlus 12 5G','Electronics',64999,69999,'OnePlus 12 with Snapdragon 8 Gen 3, 100W fast charging, Hasselblad camera.','https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=400&q=80',4.6,2190,90,'seller1','Tech Store Pro','OnePlus',1,0,0);

INSERT IGNORE INTO product_tags (product_id,tag) VALUES
('p001','smartphone'),('p001','apple'),('p001','iphone'),('p001','5g'),
('p002','smartphone'),('p002','samsung'),('p002','android'),('p002','5g'),
('p003','laptop'),('p003','apple'),('p003','macbook'),('p003','m3'),
('p004','headphones'),('p004','sony'),('p004','noise-cancelling'),
('p005','tablet'),('p005','apple'),('p005','ipad'),('p005','m2'),
('p006','smartwatch'),('p006','samsung'),('p006','health'),
('p007','smartphone'),('p007','oneplus'),('p007','5g'),('p007','android');

INSERT IGNORE INTO product_reviews (product_id,user_name,rating,comment,review_date) VALUES
('p001','Rahul K',5,'Absolutely stunning phone!','2024-01-15'),
('p002','Amit M',5,'Best Android phone!','2024-01-20'),
('p003','Sneha P',5,'Best laptop ever!','2024-02-01'),
('p004','Kiran V',5,'Magical noise cancellation!','2024-01-25'),
('p005','Divya R',5,'Perfect for work and creativity!','2024-01-28'),
('p006','Ravi S',4,'Great fitness tracker!','2024-02-03'),
('p007','Arun M',5,'Best value flagship!','2024-01-12');

-- Fashion (7)
INSERT IGNORE INTO products (id,name,category,price,original_price,description,image,rating,reviews_count,stock,seller_id,seller_name,brand,featured,trending,best_seller) VALUES
('p008','Nike Air Max 270','Fashion',7999,9999,'Nike Air Max 270 with large Air unit, breathable upper, all-day comfort.','https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80',4.5,5678,200,'seller1','Tech Store Pro','Nike',1,1,1),
('p009','Adidas Ultraboost 23','Fashion',12999,15999,'Ultraboost 23 running shoes with BOOST cushioning for energy return.','https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&q=80',4.6,3241,150,'seller1','Tech Store Pro','Adidas',1,1,0),
('p010','Levis 511 Slim Jeans','Fashion',2599,3499,'Levis 511 slim fit jeans, classic 5-pocket styling, premium denim.','https://images.unsplash.com/photo-1542272604-787c3835535d?w=400&q=80',4.4,4321,300,'seller1','Tech Store Pro','Levis',0,0,1),
('p011','Adidas Trefoil Hoodie','Fashion',3499,4499,'Classic Adidas Trefoil hoodie, soft cotton-blend fleece, kangaroo pocket.','https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=400&q=80',4.3,2134,150,'seller1','Tech Store Pro','Adidas',0,0,0),
('p012','Puma RS-X Sneakers','Fashion',6499,7999,'Puma RS-X chunky sneakers with RS cushioning technology, bold design.','https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=400&q=80',4.4,1876,120,'seller1','Tech Store Pro','Puma',1,0,0),
('p013','Tommy Hilfiger Polo Shirt','Fashion',3299,4200,'Classic Tommy Hilfiger polo in premium pique cotton. Iconic flag logo.','https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&q=80',4.5,987,180,'seller1','Tech Store Pro','Tommy Hilfiger',0,1,0),
('p014','Ray-Ban Aviator Sunglasses','Fashion',8499,10000,'Ray-Ban Classic Aviator with polarized lenses, gold metal frame.','https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&q=80',4.7,2765,90,'seller1','Tech Store Pro','Ray-Ban',0,1,1);

INSERT IGNORE INTO product_tags (product_id,tag) VALUES
('p008','shoes'),('p008','nike'),('p008','sports'),('p008','running'),
('p009','shoes'),('p009','adidas'),('p009','running'),('p009','boost'),
('p010','jeans'),('p010','levis'),('p010','denim'),('p010','casual'),
('p011','hoodie'),('p011','adidas'),('p011','casual'),('p011','winter'),
('p012','sneakers'),('p012','puma'),('p012','casual'),
('p013','polo'),('p013','tommy'),('p013','formal'),('p013','casual'),
('p014','sunglasses'),('p014','rayban'),('p014','fashion'),('p014','accessories');

INSERT IGNORE INTO product_reviews (product_id,user_name,rating,comment,review_date) VALUES
('p008','Rohit D',5,'Super comfortable!','2024-01-18'),
('p009','Meena K',5,'Best running shoes ever!','2024-01-22'),
('p010','Arjun S',5,'Perfect fit!','2024-01-30'),
('p011','Meera J',4,'Very warm!','2024-02-05'),
('p012','Kavya R',4,'Stylish and comfortable!','2024-01-14'),
('p013','Vijay N',5,'Premium quality polo!','2024-02-08'),
('p014','Pooja L',5,'Classic and stylish!','2024-01-20');

-- Books (7)
INSERT IGNORE INTO products (id,name,category,price,original_price,description,image,rating,reviews_count,stock,seller_id,seller_name,brand,featured,trending,best_seller) VALUES
('p015','Atomic Habits','Books',499,699,'James Clears #1 NYT bestseller on building good habits and breaking bad ones.','https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&q=80',4.9,12453,500,'seller1','Tech Store Pro','James Clear',1,1,1),
('p016','Rich Dad Poor Dad','Books',399,499,'Robert Kiyosakis classic on financial education and building wealth.','https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&q=80',4.7,9876,400,'seller1','Tech Store Pro','Robert Kiyosaki',0,0,1),
('p017','The Psychology of Money','Books',449,599,'Morgan Housels timeless lessons on wealth, greed, and happiness.','https://images.unsplash.com/photo-1553729459-efe14ef6055d?w=400&q=80',4.8,7654,350,'seller1','Tech Store Pro','Morgan Housel',1,1,0),
('p018','Zero to One','Books',499,650,'Peter Thiels notes on startups and how to build the future.','https://images.unsplash.com/photo-1550399105-c4db5fb85c18?w=400&q=80',4.6,4321,280,'seller1','Tech Store Pro','Peter Thiel',0,1,0),
('p019','Think and Grow Rich','Books',299,399,'Napoleon Hills classic on the philosophy of achievement and success.','https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&q=80',4.5,6543,450,'seller1','Tech Store Pro','Napoleon Hill',0,0,1),
('p020','Deep Work','Books',399,549,'Cal Newport on rules for focused success in a distracted world.','https://images.unsplash.com/photo-1592496431122-2349e0fbc666?w=400&q=80',4.7,3210,320,'seller1','Tech Store Pro','Cal Newport',1,0,0),
('p021','The Alchemist','Books',249,350,'Paulo Coelhos magical fable about following your dreams and destiny.','https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&q=80',4.8,15432,600,'seller1','Tech Store Pro','Paulo Coelho',0,1,1);

INSERT IGNORE INTO product_tags (product_id,tag) VALUES
('p015','self-help'),('p015','habits'),('p015','productivity'),
('p016','finance'),('p016','money'),('p016','investing'),
('p017','finance'),('p017','psychology'),('p017','money'),
('p018','startup'),('p018','business'),('p018','entrepreneurship'),
('p019','motivation'),('p019','success'),('p019','mindset'),
('p020','productivity'),('p020','focus'),('p020','work'),
('p021','fiction'),('p021','philosophy'),('p021','inspiration');

INSERT IGNORE INTO product_reviews (product_id,user_name,rating,comment,review_date) VALUES
('p015','Pooja R',5,'Life changing!','2024-01-12'),
('p016','Vikram N',5,'Changed my perspective!','2024-02-08'),
('p017','Ananya S',5,'Must read for everyone!','2024-01-18'),
('p018','Karthik M',5,'Brilliant startup insights!','2024-02-02'),
('p019','Suresh P',5,'Timeless wisdom!','2024-01-25'),
('p020','Riya K',5,'Changed how I work!','2024-02-06'),
('p021','Lakshmi V',5,'Beautiful and inspiring!','2024-01-08');

-- Gaming (7)
INSERT IGNORE INTO products (id,name,category,price,original_price,description,image,rating,reviews_count,stock,seller_id,seller_name,brand,featured,trending,best_seller) VALUES
('p022','PlayStation 5','Gaming',54999,59999,'PS5 with ultra-high speed SSD, ray tracing, 4K gaming, DualSense haptic feedback.','https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=400&q=80',4.8,6789,25,'seller1','Tech Store Pro','Sony',1,1,1),
('p023','Xbox Series X','Gaming',52999,55999,'Xbox Series X fastest, most powerful Xbox ever. 4K 120fps gaming.','https://images.unsplash.com/photo-1621259182978-fbf93132d53d?w=400&q=80',4.7,4532,30,'seller1','Tech Store Pro','Microsoft',0,1,0),
('p024','Nintendo Switch OLED','Gaming',34999,39999,'Nintendo Switch OLED with vibrant 7-inch OLED screen, enhanced audio.','https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?w=400&q=80',4.7,3876,45,'seller1','Tech Store Pro','Nintendo',1,1,0),
('p025','Razer BlackWidow V4 Keyboard','Gaming',12999,15999,'Razer mechanical gaming keyboard, Razer Yellow switches, RGB Chroma.','https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400&q=80',4.6,2187,70,'seller1','Tech Store Pro','Razer',0,0,1),
('p026','Logitech G502 X Mouse','Gaming',6999,8499,'Logitech G502 X gaming mouse, LIGHTFORCE hybrid switch, HERO 25K sensor.','https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&q=80',4.7,3210,90,'seller1','Tech Store Pro','Logitech',0,1,0),
('p027','SteelSeries Arctis Nova Pro','Gaming',24999,29999,'Premium gaming headset, active noise cancellation, high-fidelity audio.','https://images.unsplash.com/photo-1612198188060-c7c2a3b66eae?w=400&q=80',4.8,1654,55,'seller1','Tech Store Pro','SteelSeries',1,0,0),
('p028','PS5 DualSense Controller','Gaming',5999,6999,'Sony DualSense wireless controller with haptic feedback and adaptive triggers.','https://images.unsplash.com/photo-1593118247619-e2d6f056869e?w=400&q=80',4.8,5432,120,'seller1','Tech Store Pro','Sony',0,1,1);

INSERT IGNORE INTO product_tags (product_id,tag) VALUES
('p022','gaming'),('p022','playstation'),('p022','console'),('p022','ps5'),
('p023','gaming'),('p023','xbox'),('p023','console'),('p023','microsoft'),
('p024','gaming'),('p024','nintendo'),('p024','switch'),('p024','portable'),
('p025','keyboard'),('p025','razer'),('p025','mechanical'),('p025','rgb'),
('p026','mouse'),('p026','logitech'),('p026','gaming'),('p026','precision'),
('p027','headset'),('p027','gaming'),('p027','steelseries'),('p027','anc'),
('p028','controller'),('p028','ps5'),('p028','sony'),('p028','gaming');

INSERT IGNORE INTO product_reviews (product_id,user_name,rating,comment,review_date) VALUES
('p022','Sagar T',5,'Best console!','2024-01-08'),
('p023','Ravi K',5,'Incredible!','2024-01-22'),
('p024','Sneha M',5,'Perfect portable gaming!','2024-01-16'),
('p025','Arjun T',5,'Amazing tactile feel!','2024-02-04'),
('p026','Rahul S',5,'Best gaming mouse!','2024-01-28'),
('p027','Divya P',5,'Crystal clear audio!','2024-02-09'),
('p028','Varun L',5,'Haptic feedback is insane!','2024-02-01');

-- Home Appliances (7)
INSERT IGNORE INTO products (id,name,category,price,original_price,description,image,rating,reviews_count,stock,seller_id,seller_name,brand,featured,trending,best_seller) VALUES
('p029','LG OLED Smart TV 55"','Home Appliances',129999,149999,'LG 55-inch 4K OLED TV, ThinQ AI, Dolby Vision IQ, perfect black levels.','https://images.unsplash.com/photo-1593359677879-a4bb92f829e1?w=400&q=80',4.8,3210,20,'seller1','Tech Store Pro','LG',1,1,1),
('p030','Samsung Double Door Refrigerator','Home Appliances',45999,52999,'Samsung 253L frost-free refrigerator, Digital Inverter, Twin Cooling Plus.','https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&q=80',4.5,1987,20,'seller1','Tech Store Pro','Samsung',0,0,0),
('p031','Dyson V15 Detect Vacuum','Home Appliances',54999,64999,'Dyson V15 cordless vacuum with laser dust detection, powerful suction.','https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&q=80',4.7,876,35,'seller1','Tech Store Pro','Dyson',1,1,0),
('p032','Instant Pot Duo 7-in-1','Home Appliances',8999,11999,'7-in-1 electric pressure cooker, slow cooker, rice cooker and more.','https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&q=80',4.6,4321,80,'seller1','Tech Store Pro','Instant Pot',0,1,1),
('p033','Philips Air Fryer XXL','Home Appliances',14999,18999,'Philips Air Fryer with Rapid Air technology, 7.3L capacity, digital display.','https://images.unsplash.com/photo-1585577697835-fbc50dc49d2b?w=400&q=80',4.5,2876,60,'seller1','Tech Store Pro','Philips',0,0,1),
('p034','Bosch Front Load Washing Machine','Home Appliances',42999,49999,'Bosch 7kg front load washing machine, EcoSilence Drive, anti-vibration.','https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&q=80',4.6,1543,15,'seller1','Tech Store Pro','Bosch',0,0,0),
('p035','Nespresso Vertuo Coffee Machine','Home Appliances',17999,21999,'Nespresso Vertuo, centrifusion brewing technology, makes 5 cup sizes.','https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&q=80',4.7,2109,45,'seller1','Tech Store Pro','Nespresso',1,1,0);

INSERT IGNORE INTO product_tags (product_id,tag) VALUES
('p029','tv'),('p029','lg'),('p029','oled'),('p029','4k'),
('p030','refrigerator'),('p030','samsung'),('p030','fridge'),
('p031','vacuum'),('p031','dyson'),('p031','cordless'),('p031','cleaning'),
('p032','cooker'),('p032','kitchen'),('p032','instant-pot'),('p032','pressure'),
('p033','airfryer'),('p033','philips'),('p033','kitchen'),('p033','healthy'),
('p034','washing-machine'),('p034','bosch'),('p034','laundry'),
('p035','coffee'),('p035','nespresso'),('p035','kitchen'),('p035','espresso');

INSERT IGNORE INTO product_reviews (product_id,user_name,rating,comment,review_date) VALUES
('p029','Sunita B',5,'Outstanding picture!','2024-02-03'),
('p030','Deepa M',4,'Energy efficient!','2024-01-28'),
('p031','Priya M',5,'Incredible suction power!','2024-01-15'),
('p032','Neha S',5,'Game changer for cooking!','2024-02-07'),
('p033','Kavitha R',5,'Crispy without oil!','2024-01-21'),
('p034','Anjali P',5,'Silent and efficient!','2024-02-11'),
('p035','Ritu L',5,'Perfect coffee every time!','2024-01-30');

-- Sports (7)
INSERT IGNORE INTO products (id,name,category,price,original_price,description,image,rating,reviews_count,stock,seller_id,seller_name,brand,featured,trending,best_seller) VALUES
('p036','Professional Cricket Bat MSD','Sports',4999,5999,'MSD Edition English Willow cricket bat, SS Ton, full ready-to-play.','https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=400&q=80',4.6,1234,80,'seller1','Tech Store Pro','SS Ton',1,1,1),
('p037','Nivia Pro Football','Sports',1499,1999,'Nivia Pro match football, FIFA quality pro approved, size 5.','https://images.unsplash.com/photo-1614632537197-38a17061c2bd?w=400&q=80',4.4,2134,150,'seller1','Tech Store Pro','Nivia',0,0,0),
('p038','Yonex Astrox 100 Badminton Racket','Sports',8999,10999,'Yonex Astrox 100 ZZ badminton racket, used by top professionals.','https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=400&q=80',4.8,876,60,'seller1','Tech Store Pro','Yonex',1,1,0),
('p039','Cosco Basketball Size 7','Sports',1299,1699,'Cosco official size basketball, rubber material, ideal for outdoor courts.','https://images.unsplash.com/photo-1546519638405-a9e9e6dde8df?w=400&q=80',4.3,765,100,'seller1','Tech Store Pro','Cosco',0,0,0),
('p040','Decathlon Yoga Mat Premium','Sports',1999,2499,'Decathlon premium yoga mat, 6mm thick, anti-slip, carrying strap included.','https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400&q=80',4.5,3421,200,'seller1','Tech Store Pro','Decathlon',0,1,1),
('p041','Boldfit Adjustable Dumbbells Set','Sports',4499,5999,'Boldfit adjustable dumbbell set 2-20kg, home gym essentials.','https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&q=80',4.4,1876,70,'seller1','Tech Store Pro','Boldfit',1,0,0),
('p042','Garmin Forerunner 255 Watch','Sports',29999,34999,'Garmin running watch with advanced training metrics, GPS, 14-day battery.','https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=400&q=80',4.7,1234,40,'seller1','Tech Store Pro','Garmin',0,1,0);

INSERT IGNORE INTO product_tags (product_id,tag) VALUES
('p036','cricket'),('p036','bat'),('p036','sports'),
('p037','football'),('p037','sports'),('p037','nivia'),
('p038','badminton'),('p038','racket'),('p038','yonex'),('p038','sports'),
('p039','basketball'),('p039','cosco'),('p039','sports'),('p039','outdoor'),
('p040','yoga'),('p040','mat'),('p040','fitness'),('p040','decathlon'),
('p041','dumbbells'),('p041','fitness'),('p041','gym'),('p041','weights'),
('p042','garmin'),('p042','running'),('p042','gps'),('p042','watch');

INSERT IGNORE INTO product_reviews (product_id,user_name,rating,comment,review_date) VALUES
('p036','Suresh P',5,'Great balance!','2024-02-10'),
('p037','Aakash G',4,'Good quality!','2024-01-05'),
('p038','Deepak R',5,'Pro-level performance!','2024-01-19'),
('p039','Vikrant M',4,'Good grip!','2024-02-06'),
('p040','Priya S',5,'Perfect grip and cushion!','2024-01-26'),
('p041','Raj K',4,'Great for home workouts!','2024-02-03'),
('p042','Arun V',5,'Best running GPS!','2024-01-15');
 