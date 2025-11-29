from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ===================== MODELS =========================

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    users = db.relationship('User', backref='department', lazy=True)




class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)

    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  

    gender = db.Column(db.String(20), nullable=True)   # <-- NEW COLUMN

    date_created = db.Column(db.DateTime, default=datetime.utcnow)



class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='scheduled')



# ===================== AUTH HELPERS =========================



def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))

            if role and session.get('role') != role:
                return "Unauthorized Access"

            return fn(*args, **kwargs)
        return decorated
    return wrapper




# ===================== AUTH ROUTES =========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        gender = request.form['gender']    # <-- NEW LINE

        new_user = User(
            username=username,
            email=email,
            password=password,
            role="patient",
            gender=gender                   # <-- SAVE GENDER
        )

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



# ===================== ADMIN ROUTES =========================

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    doctors = User.query.filter_by(role='doctor').all()
    patients = User.query.filter_by(role='patient').all()
    appointments = Appointment.query.all()

    return render_template(
        'admin_dashboard.html',
        doctors=doctors,
        patients=patients,
        appointments=appointments
    )


@app.route('/admin/add_doctor', methods=['POST'])
@login_required(role='admin')
def add_doctor():
    username = request.form['username']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])

    doctor = User(username=username, email=email, password=password, role="doctor")
    db.session.add(doctor)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))



# ===================== DOCTOR ROUTES =========================

@app.route('/doctor/dashboard')
@login_required(role='doctor')
def doctor_dashboard():
    id = session['user_id']
    appointments = Appointment.query.filter_by(doctor_id=id).all()
    return render_template('doctor_dashboard.html', appointments=appointments)



# ===================== PATIENT ROUTES =========================

@app.route('/patient/dashboard')
@login_required(role='patient')
def patient_dashboard():
    id = session['user_id']
    appointments = Appointment.query.filter_by(patient_id=id).all()
    doctors = User.query.filter_by(role='doctor').all()

    return render_template(
        'patient_dashboard.html',
        appointments=appointments,
        doctors=doctors
    )


@app.route('/patient/book/<doctor_id>', methods=['POST'])
@login_required(role='patient')
def book(doctor_id):
    patient_id = session['user_id']
    date = request.form['date']
    time = request.form['time']
    dt = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")

    new_app = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        datetime=dt
    )

    db.session.add(new_app)
    db.session.commit()

    return redirect(url_for('patient_dashboard'))



# ===================== RUN APP =========================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create Admin if not exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@gmail.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
















