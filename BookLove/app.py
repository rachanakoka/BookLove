from flask import Flask, request,render_template, redirect,session
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))
    usertype = db.Column(db.String(6))

    def __init__(self, email, password, name, usertype, userbooks=None):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.usertype = usertype
    

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Book(db.Model):
    id = db.Column(db.Integer)
    bookname = db.Column(db.String(100), primary_key=True)
    price = db.Column(db.String(6))
    originalprice = db.Column(db.String(6))
    author = db.Column(db.String(100), nullable=False)

    def __init__(self,bookname,price,originalprice,author):
        self.bookname = bookname
        self.price = price
        self.originalprice = originalprice
        self.author =author

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookname = db.Column(db.String(100), db.ForeignKey('book.bookname')) 
    username = db.Column(db.String(100), db.ForeignKey('user.name'))     
    issue = db.Column(db.String(1), default='0')

    def __init__(self,bookname,username,issue='0'):
        self.bookname = bookname
        self.username = username
        self.issue = issue
        
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookname = db.Column(db.String(100), db.ForeignKey('book.bookname')) 
    username = db.Column(db.String(100), db.ForeignKey('user.name'))     
    feedback = db.Column(db.String(200))

    def __init__(self,bookname,username,feedback):
        self.bookname = bookname
        self.username = username
        self.feedback = feedback

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    books = books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        usertype = request.form['usertype']
        new_user = User(name=name,email=email,password=password,usertype=usertype)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')



    return render_template('register.html')

@app.route('/addbooks',methods=['GET','POST'])
def addbooks():
    if request.method == 'POST':
        # handle request
        bookname = request.form['bookname']
        price = request.form['price']
        originalprice = request.form['originalprice']
        author = request.form['author']
        new_book = Book(bookname=bookname,price=price,originalprice=originalprice,author=author)
        db.session.add(new_book)
        db.session.commit()
    return render_template('addbooks.html')

@app.route('/borrowbook', methods=['GET', 'POST'])
def borrowbook():
    if request.method == 'POST':
        username = request.form['username']
        bookname = request.form['bookname']
        if Borrow.query.filter_by(username=username).count() <5:
            new_book = Borrow(bookname=bookname, username=username)
            db.session.add(new_book)
            db.session.commit()
            
        return redirect('/shop') 


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        usertype = request.form['usertype']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            if usertype == 'user':
                return redirect('/dashboard')
            elif usertype == 'admin':
                return redirect('/admin')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')

@app.route('/feedback',methods=['GET','POST'])
def feedback():
    if request.method == 'POST':
        # handle request
        bookname = request.form['bookname']
        username = request.form['username']
        feedback = request.form['feedback']
        new_feedback = Feedback(bookname=bookname,username=username,feedback=feedback)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect('/shop')
    return redirect('/shop') 


@app.route('/dashboard')
def dashboard():
    if session['email']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html',user=user)
    
    return redirect('/login')

@app.route('/verify')
def verify():
    borrowed = Borrow.query.all()
    return render_template('verify.html',borrowed=borrowed)

@app.route('/admin')
def admin():
    if session['email']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('admin.html',user=user)
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')


@app.route('/shop')
def shop():
    books = Book.query.all()
    f = Feedback.query.all()
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user:
            borrowed_books = Borrow.query.filter_by(username=user.name).all()
    return render_template('shop.html', books=books, borrowed_books=borrowed_books,f=f)

from sqlalchemy import or_

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        # Perform a database query to search for books
        books = Book.query.filter(or_(Book.bookname.ilike(f"%{query}%"), Book.author.ilike(f"%{query}%"))).all()
    else:
        books = Book.query.all()
    return render_template('search_results.html', books=books, query=query)

@app.route('/verified/<int:borrow_id>')
def verified(borrow_id):
    borrowed = Borrow.query.get(borrow_id)
    if borrowed:
        borrowed.issue = '1'
        db.session.commit()
    return redirect('/verify')

@app.route('/returned/<int:borrow_id>')
def returned(borrow_id):
    borrowed = Borrow.query.get(borrow_id)
    if borrowed:
        borrowed.issue = '0'
        db.session.commit()
        db.session.delete(borrowed)  
        db.session.commit()
    return redirect('/shop')


if __name__ == '__main__':
    app.run(debug=True)