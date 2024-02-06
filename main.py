from flask import Flask, render_template, redirect, url_for,flash,request,make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from flask_login import UserMixin,login_user,login_remembered,login_required,logout_user,current_user,LoginManager
import random
app = Flask(__name__)
app.config['TESTING'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    image_href = db.Column(db.String(200), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)



class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.cart_id'), nullable=False)
    cart = db.relationship('Cart', backref=db.backref('user', lazy=True))


class CartProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.cart_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)




@app.route('/')
def landing():
    return render_template('home.html')



@app.route('/checkout')
@login_required
def checkout():
    checkout_user_id = current_user.id
    checkout_user = db.session.get(User,checkout_user_id)
    checkout_cart_id = checkout_user.cart_id
    cart = db.session.query(CartProduct).filter_by(cart_id=checkout_cart_id).all()
    product_names = []

    total_price = 0.0
    for cart_item in cart:
        product = db.session.query(Product).filter_by(product_id=cart_item.product_id).first()
        total_price = total_price + cart_item.price
        if product:
            product_names.append(product.product_name)

    cart_length = len(cart)




    return render_template('checkout.html', cart=cart, total_price=total_price,cart_length=cart_length,product_names=product_names)


@app.route('/product/<int:product_id>',methods=['POST','GET'])
def product_detail(product_id):
    product = db.session.get(Product,product_id)
    logged_user = db.session.get(User,current_user.id)
    logged_cart_id = logged_user.cart_id
    transaction_id = random.randrange(10**7, 10**8)
    if request.method == 'POST':
        quantity  = request.form.get('quantity')
        quantity = int(quantity)
        price = quantity * product.price
        transaction = CartProduct(id=transaction_id,cart_id=logged_cart_id,product_id=product_id,quantity=quantity,price=price)
        db.session.add(transaction)
        db.session.commit()
        flash('Added to cart','success')

    return render_template('product.html', product=product)

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user.password == password:
            login_user(user)
           
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password == confirm_password:
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash('User exists')
                return redirect(url_for('register'))
            else:
                user_id = random.randrange(10**7, 10**8)
                cart_id = random.randrange(10**7, 10**8)
                new_user = User(id=user_id,username=username,email=email,password=password,cart_id=cart_id)
                db.session.add(new_user)
                db.session.commit()
                cookie_value = str(user_id)
                response = make_response(render_template('login.html'))
                response.set_cookie('user_id', value=cookie_value, max_age=3600)  # max_age is in seconds
                return response
        else:
            flash("Passwords doesn't")
    return render_template('register.html')



@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.all()
    return render_template('dashboard.html', products=products)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
