from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import qrcode
from io import BytesIO
import os
import base64

# --Flask Setup--
app = Flask(__name__)
app.secret_key = 'secretkey'

# Use absolute path for SQLite (avoids multiple DBs issue)
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --Creating Database Model--
class User(db.Model):
    _tablename_ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)


class QRCodeData(db.Model):
    _tablename_ = 'qr_code_data'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# ---Here we Create Tables to store Data 
# Put this inside app context which forces table creation properly
with app.app_context():
    print("Creating all tables...")
    db.create_all()
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("Tables:", inspector.get_table_names())


# --Routes of app--
        #  route of home
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')
        # route of about
@app.route('/about')
def about():
    return render_template('/about.html')
       
        # route of Profile
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    user_id=session['user_id']
    user=User.query.get(user_id)
    qr_count=QRCodeData.query.filter_by(user_id=user_id).count()
    return render_template("profile.html",user=user,qr_count=qr_count) 

        # route of login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect('/')
        else:
            return "Invalid login. Try again!"
    return render_template('login.html')

        # route of Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('signup.html')

        # route of History
@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id=session['user_id']
    qr_list=QRCodeData.query.filter_by(user_id=user_id).all()     
    return render_template('history.html',qr_list=qr_list)  

        # route of Delete
@app.route('/delete/<int:qr_id>')
def delete_qr(qr_id):
    if 'user_id' not in session:
        return redirect('/login')
    qr=QRCodeData.query.get_or_404(qr_id)
    if qr.user_id == session['user_id']:
        db.session.delete(qr)
        db.session.commit()
    return redirect('/history')                
              
        # route of Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

        # route of Generate ___to generate qr code on index page
@app.route('/generate', methods=['POST'])
def generate():
    if 'user_id' not in session:
        return redirect('/login')

    text = request.form['text']
    qrdata = QRCodeData(text=text, user_id=session['user_id'])
    db.session.add(qrdata)
    db.session.commit()

    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('index.html', qr_image=qr_image, text=text)


if __name__ == '__main__':
    app.run(debug=True)