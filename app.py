import io
import csv
from flask import Flask , render_template , redirect ,url_for,request , Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,logout_user, current_user,login_required
from werkzeug.security import generate_password_hash,check_password_hash

app =Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///stockflow.db'
app.config['SECRET_KEY']='mlh_secure_aaccess_2025'
db=SQLAlchemy(app)

# Authentication Setup

login_manager =LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Database Models
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100),unique=True ,nullable=False)
    password = db.Column(db.String(200),nullable=False)
    role = db.Column(db.String(20),default ='staff')   #admin or staff

class Employee(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    full_name = db.Column(db.String(100),nullable = False)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    email = db.Column(db.String(100))


# Routes

@app.route('/login',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username = request.form['username']).first()
        if user and check_password_hash(user.password,request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html') 


@app.route('/')
@login_required
def dashboard():
    # fetching all employees to display on table
    employees = Employee.query.all()
    return render_template('dashboard.html',employees=employees)


@app.route('/add_employee',methods = ['POST'])
@login_required
def add_employee():
    # only Admin can Add Employees
    if current_user.role == 'admin':
        new_emp = Employee (
            full_name = request.form['full_name'],
            department = request.form['department'],
            position = request.form['position'],
            email = request.form['email']
        )
        db.session.add(new_emp)
        db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/export_staff')
@login_required
def export_staff():
    employees = Employee.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','Name','Department','Position','Email'])  
    for e in employees:
         writer.writerow([e.id,e.full_name,e.department,e.position,e.email])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-discussion":"attachment;filename = staff_report.csv"}
    )

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/delete/<int:emp_id>')
@login_required
def delete_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)

    # Optional: Admin-only protection
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    db.session.delete(employee)
    db.session.commit()

    return redirect(url_for('dashboard'))

#  Initialize System
with app.app_context():
    db. create_all()
    # create default admin if not exist
    if not User.query.filter_by(username = 'admin').first():
        hashed_pw = generate_password_hash('admin123',method='pbkdf2:sha256')
        admin = User(username='admin',password = hashed_pw, role='admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug = True)


       