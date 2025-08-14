
from flask import Flask, render_template, request, redirect, url_for, flash, session,abort
from datetime import datetime
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from pymongo import MongoClient
from uuid import uuid4
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# === MongoDB Config ===
MONGO_URI = os.getenv('MONGO_URI')
print(MONGO_URI)
client = MongoClient(MONGO_URI)
db = client['shop']
users_col = db["users"]
products_col = db["products"]
wishlist_items = [] # Your global or session wishlist list
products_collection = db['products']
wishlist_collection = db["wishlist"]



# === File Upload Config ===
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# === Sample Product Data ===
WATCHES = [
    {"name": "ChronoX Sport", "price": 2000, "offer": "15% off", "delivery": "Delivery by June 18, 2025", "image": "watches1.jpg"},
    {"name": "Elegance Leather", "price": 50000, "offer": "10% off", "delivery": "Delivery by June 20, 2025", "image": "watch2.jpeg"},
    {"name": "AeroPilot Chrono", "price": 10000, "offer": "20% off", "delivery": "Delivery by June 22, 2025", "image": "watch3.png"},
]

DRESSES = [
    {"name": "Red Summer Dress", "price": 1500, "offer": "25% off", "delivery": "Delivery by June 20, 2025", "image": "dress1.jpg"},
    {"name": "Evening Gown", "price": 3500, "offer": "30% off", "delivery": "Delivery by June 21, 2025", "image": "dress2.jpg"},
    {"name": "Casual Denim Dress", "price": 1800, "offer": "10% off", "delivery": "Delivery by June 30, 2025", "image": "dress3.jpeg"}
]

BEAUTY = [
    {"name": "Herbal Face Wash", "price": 250, "offer": "10% off", "delivery": "Delivery by June 19, 2025", "image": "beauty1.jpg"},
    {"name": "Lipstick Set", "price": 800, "offer": "15% off", "delivery": "Delivery by June 20, 2025", "image": "beauty2.jpg"},
    {"name": "Glow Radiance Serum", "price": 3500, "offer": "30% off", "delivery": "Delivery by June 21, 2025", "image": "beauty3.jpg"},
]

# === Home Page ===
@app.route('/')
def home():
    return render_template('home.html')

# === User Login ===

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check hardcoded user credentials
        if username == 'user' and password == 'pass':
            session['username'] = username
            session['role'] = 'user'  # Set role in session
            flash('Login successful!', 'success')
            return redirect(url_for('category_page'))  # ✅ Corrected here
        else:
            flash('Invalid credentials.', 'error')

    return render_template('user_login.html')



# === Logout ===
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/categories')
def category_page():
    if 'username' in session and session.get('role') == 'user':
        return render_template('categories.html', username=session['username'])
    return redirect(url_for('user_login'))




# === User Register ===
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!", "error")
        elif username == "" or email == "":
            flash("Please fill all required fields!", "error")
        else:
            flash("Registration successful!", "success")
            return redirect(url_for('user_register'))
    return render_template("user_register.html")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Admin credentials check
        if username == 'admin' and password == 'admin123':
            session['username'] = username
            session['role'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('add_product'))  # Redirect to admin page
        else:
            flash('Invalid admin credentials.', 'error')

    # Ensure this is returned on GET or after failed login
    return render_template('admin_login.html')

# === Admin Add Product ===
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        offer = request.form.get('offer')
        category = request.form.get('category')
        image = request.files.get('image')

        if not (name and description and price and offer and category and image):
            flash("All fields are required.", "error")
            return redirect(url_for('add_product'))

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        product_data = {
            'name': name,
            'description': description,
            'price': int(price),
            'offer': int(offer),
            'category': category,
            'added_on': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'image_filename': filename
        }

        # Save to MongoDB
        products_col.insert_one(product_data)

        flash(f"'{name}' added to {category} successfully!", "success")
        
        # Redirect based on category
        if category == "Watches":
            return redirect(url_for('watches'))
        elif category == "Dresses":
            return redirect(url_for('dresses'))
        elif category == "Beauty":
            return redirect(url_for('beauty'))
        else:
            return redirect(url_for('home'))

    return render_template("add_product.html")

@app.route('/admin/products')
def admin_products():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('home'))

    products = products_col.find()
    return render_template('admin_products.html', products=products)



# === Category Dynamic View ===
@app.route('/category/<category_name>')
def show_category(category_name):
    products = products_col.find({'category': category_name})
    return render_template(f"{category_name.lower()}.html", products=products)


# === Product Category Pages ===
@app.route('/watches')
def watches():
    products = products_col.find({'category': 'Watches'})
    return render_template('watches.html', products=products)

@app.route('/dresses')
def dresses():
    products = products_col.find({'category': 'Dresses'})
    return render_template('dresses.html', products=products)

@app.route('/beauty')
def beauty():
    products = products_col.find({'category': 'Beauty'})
    return render_template('beauty.html', products=products)


@app.route('/buy', methods=['POST'])
def buy_product():
    # Check if someone is logged in
    if 'username' not in session:
        flash("Please login to place an order.", "error")
        return redirect(url_for('user_login'))
    
    # Check if the logged-in user is NOT an admin
    if session.get('role') != 'user':
        flash("Admins cannot place orders. Please login as a user.", "error")
        return redirect(url_for('user_login'))

    product_name = request.form.get('name')
    flash(f"Order placed successfully for {product_name}!", "success")
    return redirect(url_for('place_order'))




#  Place Order
@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        print(f"Order received: {name}, {address}, {phone}")
        flash("✅ Order placed successfully!", "success")
        return redirect(url_for('place_order'))
    return render_template('place_order.html')

    
@app.route('/product/<category>/<name>')
def product_detail(category, name):
    category = category.lower()
    products = {
        'watches': WATCHES,
        'dresses': DRESSES,
        'beauty': BEAUTY
    }

    product_list = products.get(category, [])
    selected = next((p for p in product_list if p['name'] == name), None)

    if not selected:
        return "<h3>Product not found.</h3>"

    return render_template('product_detail.html', product=selected, category=category)

@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    product = {
        'name': request.form['name'],
        'price': int(request.form['price']),
        'image': request.form['image'],
        'category': request.form['category']
    }

    if 'wishlist' not in session:
        session['wishlist'] = []

    session['wishlist'].append(product)
    session.modified = True

    flash(f"Added {product['name']} to wishlist.", "info")
    return redirect(url_for('wishlist'))

@app.route('/wishlist')
def wishlist():
    wishlist_items = session.get('wishlist', [])
    return render_template('wishlist.html', wishlist=wishlist_items)


@app.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    if session.get('role') != 'admin':
        flash("Only admin can delete products.", "error")
        return redirect(url_for('user_login'))

    db.products.delete_one({'_id': ObjectId(product_id)})
    flash("Product removed successfully!", "success")
    return redirect(url_for('watches')) 

@app.route('/product/<product_id>')
def view_product_detail(product_id):
    try:
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            abort(404)
        return render_template('product_detail.html', product=product)
    except:
        abort(404)



# === Run Server === #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port, debug=True)
