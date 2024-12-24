from models import db, User, District, Hospital, Assistant, Doctor, Nurse, Patient, Appointment
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string


# # Data structures

# users = {
#     "admin": {"password": generate_password_hash("admin123"), "role": "admin"},
#     "doctor1": {"password": generate_password_hash("doctor123"), "role": "doctor"},
#     "patient1": {"password": generate_password_hash("patient123"), "role": "patient"},
#     "headnurse1": {"password": generate_password_hash("nurse123"), "role": "head_nurse"},
#     "assistant1": {"password": generate_password_hash("assistant123"), "role": "assistant"}

# }

# # Districts
# districts = {
#     "district1": {
#         "name": "District 1",
#         "hospitals": ["hospital1"]
#     },
#     "district2": {
#         "name": "District 2",
#         "hospitals": ["hospital2"]
#     }
# }

# # Assistants data structure
# assistants = {
#     "assistant1": {
#         "name": "Assistant One",
#         "hospital": "hospital1"
#     }
# }

# # Updated Doctors
# doctors = {
#     "doctor1": {
#         "name": "Smith",
#         "specialty": "Cardiology",
#         "note": "Senior Cardiologist.",
#         "hospital": "hospital1",
#         "district": "district1"
#     }
# }

# # Updated Nurses
# nurses = {
#     "headnurse1": {
#         "name": "Nurse Jane",
#         "note": "Head Nurse in the ICU.",
#         "hospital": "hospital1",
#         "district": "district1"
#     }
# }

# # Updated Patients
# patients = {
#     "patient1": {
#         "name": "John",
#         "age": 30,
#         "gender": "Male",
#         "appointments": [1],
#         "note": "Patient requires regular check-ups.",
#         "covid": True,
#         "hospital": None,  # Assigned during registration
#         "district": "district1",  # Assigned during registration
#         "status": "in wait"  # New status field
#     }
# }


# appointments = {
#     1: {
#         "patient": "patient1",
#         "doctor": "doctor1",
#         "date": "2024-03-31",
#         "time": "23:42",
#         "status": "scheduled"
#     }
# }

# # Hospital data structure
# hospitals = {
#     "hospital1": {
#         "name": "Hospital 1",
#         "total_beds": 20,
#         "beds": [None for _ in range(20)]  # Initialize all beds as unoccupied
#     },
#     "hospital2": {
#         "name": "Hospital 2",
#         "total_beds": 10,
#         "beds": [None for _ in range(10)]  # Initialize all beds as unoccupied
#     }
# }


# Web routes and API

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config.from_object('config')
db.init_app(app)
# Create the application context
with app.app_context():
    db.create_all()
    db.session.commit()

    def add_admin():
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print('Admin user created successfully.')
        else:
            print('Admin user already exists.')
    def admin_check():
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            print('No admin user found. Please create an admin user. Creating admin user with default password "admin123"...')
            # Execute the add_admin function
            add_admin()

        else:
            print('Admin user found.')

    # Execute the admin check function
    admin_check()

# Home page route
@app.route('/')
def index():
    current_year = datetime.now().year
    username = session.get('username', None)
    role = session.get('role', None)
    return render_template('index.html', username=username, role=role, current_year=current_year)

@app.errorhandler(404)
def not_found(error):
    """This function returns error response template for users"""
    flash('The requested resource was not found.')
    return redirect(url_for('dashboard'))

def generate_unique_id(prefix, length=10):
    return prefix + ''.join(random.choices(string.digits, k=length))


@app.route('/user/<username>', methods=['GET', 'POST'])
def profile(username):
    # Look up the user (could be a patient or doctor) by username
    user = User.query.filter_by(username=username).first()

    # If the user is not found, flash an error and redirect
    if not user:
        flash(f'User {username} not found!')
        return redirect(url_for('index'))

    # Get the role of the logged-in user from the session
    role = session.get('role')

    # Admin can access all user data, including all appointments, notes, and COVID status
    if role == 'admin':
        user_data = user.to_dict()
        user_data["appointments"] = [
            appt.to_dict() for appt in Appointment.query.filter_by(patient_id=user.id).all()
        ]
        return render_template('patient_profile.html', **user_data)

    # Fetch patient-specific appointments, notes, and COVID status for doctors, head nurses, and admins
    if role in ['admin', 'doctor', 'head_nurse']:
        user_data = user.to_dict()
        user_data["appointments"] = [
            appt.to_dict() for appt in Appointment.query.filter_by(patient_id=user.id).all()
        ]

        # Handle doctor POST request to update notes, covid status, and patient status
        if request.method == 'POST' and role == 'doctor' and user.role == 'patient':
            note = request.form.get('note')
            covid_status = request.form.get('covid')
            status = request.form.get('status')

            # Update the patient's notes, COVID status, and status
            if note:
                user.note = note

            if covid_status in ['True', 'False']:
                user.covid = covid_status == 'True'

            if status in ['in wait', 'accepted', 'negative', 'positive', 'healthy', 'dead']:
                user.status = status

            db.session.commit()
            flash(f'Patient {username} updated successfully!', 'success')
            return redirect(url_for('profile', username=username))

        return render_template('patient_profile.html', **user_data)

    # Doctors can view patient details and their appointments if the user is a patient
    elif role == 'doctor' and user.role == 'patient':
        user_data = user.to_dict()
        user_data["appointments"] = [
            appt.to_dict() for appt in Appointment.query.filter_by(patient_id=user.id).all()
        ]
        return render_template('patient_profile.html', **user_data)

    # Head nurses can view patient details and appointments related to the user
    elif role == 'head_nurse' and user.role == 'patient':
        user_data = user.to_dict()
        user_data["appointments"] = [
            appt.to_dict() for appt in Appointment.query.filter_by(patient_id=user.id).all()
        ]
        return render_template('patient_profile.html', **user_data)

    # Handle unauthorized access
    flash('Unauthorized access to this profile.')
    return redirect(url_for('dashboard'))

@app.route('/patient_details/<username>', methods=['GET'])
def patient_details(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Patient not found!')
        return redirect(url_for('dashboard'))

    # Render patient profile for doctors, nurses, and admins
    role = session.get('role')
    if role in ['doctor', 'head_nurse', 'admin']:
        patient_appointments = Appointment.query.filter_by(patient_id=user.id).all()
        patient_data = {
            "user": user.to_dict(),
            "appointments": [appt.to_dict() for appt in patient_appointments],
            "notes": user.note,
            "covid_status": user.covid,
            "status": user.status
        }
        return render_template('patient_profile.html', **patient_data)

    flash('Unauthorized access to this profile.')
    return redirect(url_for('dashboard'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if user exists and the password is correct
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            # Set user session data
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username/password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    username = session.get('username')
    role = session.get('role')

    if not username:
        flash('Please log in to access the dashboard.')
        return redirect(url_for('login'))

    # Context initialization
    context = {}

    # Admin dashboard
    if role == 'admin':
        nurses_data = {nurse.username: nurse.to_dict() for nurse in Nurse.query.all()}
        assistants_data = {assistant.username: assistant.to_dict() for assistant in Assistant.query.all()}
        doctors_data = {doctor.username: doctor.to_dict() for doctor in Doctor.query.all()}
        patients_data = {patient.username: patient.to_dict() for patient in Patient.query.all()}
        hospitals_data = {hospital.id: hospital.to_dict() for hospital in Hospital.query.all()}
        appointments_data = {appointment.id: appointment.to_dict() for appointment in Appointment.query.all()}
        districts_data = {district.id: district.to_dict() for district in District.query.all()}

        context.update({
            'appointments': appointments_data,
            'nurses': nurses_data,
            'assistants': assistants_data,
            'doctors': doctors_data,
            'patients': patients_data,
            'hospitals': hospitals_data,
            'districts': districts_data
        })
        return render_template('dashboard_admin.html', **context)

    # Doctor dashboard
    elif role == 'doctor':
        doctor = Doctor.query.filter_by(username=username).first()
        if not doctor:
            flash('Doctor not found!')
            return redirect(url_for('index'))

        doctor_district = doctor.district_id
        doctor_appointments = [
            appt.to_dict() for appt in Appointment.query.filter_by(doctor_id=doctor.id).all()
            if Patient.query.get(appt.patient_id).district_id == doctor_district
        ]

        context.update({
            'doctor': doctor.to_dict(),
            'appointments': doctor_appointments,
            'patients': {patient.username: patient.to_dict() for patient in Patient.query.filter_by(district_id=doctor_district).all()},
            'hospitals': {hospital.name: hospital.to_dict() for hospital in Hospital.query.filter_by(district_id=doctor_district).all()}
        })
        return render_template('dashboard_doctor.html', **context)

    # Patient dashboard
    elif role == 'patient':
        patient = Patient.query.filter_by(username=username).first()
        if not patient:
            flash('Patient not found!')
            return redirect(url_for('index'))

        patient_district = patient.district_id
        patient_appointments = [
            {
                **appt.to_dict(),
                'doctor_name': Doctor.query.get(appt.doctor_id).name
            }
            for appt in Appointment.query.filter_by(patient_id=patient.id).all()
        ]

        context.update({
            'patient': patient.to_dict(),
            'appointments': patient_appointments,
            'doctors': {doctor.username: doctor.to_dict() for doctor in Doctor.query.filter_by(district_id=patient_district).all()}
        })
        return render_template('dashboard_patient.html', **context)

    # Head Nurse dashboard
    elif role == 'head_nurse':
        nurse = Nurse.query.filter_by(username=username).first()
        if not nurse:
            flash('Nurse not found!')
            return redirect(url_for('index'))

        nurse_district = nurse.district_id
        nurse_appointments = [
            {
                'id': appt.id,
                'patient_name': Patient.query.get(appt.patient_id).name,
                'doctor_name': Doctor.query.get(appt.doctor_id).name,
                'date': appt.date.strftime('%Y-%m-%d'),
                'time': appt.time.strftime('%H:%M:%S'),
                'covid_status': Patient.query.get(appt.patient_id).covid,
                'patient_notes': Patient.query.get(appt.patient_id).note,
                'patient_status': Patient.query.get(appt.patient_id).status
            }
            for appt in Appointment.query.all()
            if Patient.query.get(appt.patient_id).district_id == nurse_district
        ]

        context.update({
            'appointments': nurse_appointments,
            'hospitals': {hospital.name: hospital.to_dict() for hospital in Hospital.query.all()},
            'patients': {patient.username: patient.to_dict() for patient in Patient.query.filter_by(district_id=nurse_district, covid=True).all()}
        })
        return render_template('dashboard_head_nurse.html', **context)

    # Assistant dashboard
    elif role == 'assistant':
        context.update({
            'doctors': {doctor.username: doctor.to_dict() for doctor in Doctor.query.all()},
            'nurses': {nurse.username: nurse.to_dict() for nurse in Nurse.query.all()},
            'hospitals': {hospital.name: hospital.to_dict() for hospital in Hospital.query.all()}
        })
        return render_template('dashboard_assistant.html', **context)

    # Unauthorized role or access
    flash('Unauthorized access!')
    return redirect(url_for('index'))

@app.route('/add_hospital', methods=['GET', 'POST'])
def add_hospital():
    if session.get('role') != 'admin':
        flash('Only administrators can add hospitals.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        total_beds = request.form['total_beds']
        district_id = request.form.get('district_id')

        if not name or not total_beds or not district_id:
            flash('All fields are required!')
            return redirect(url_for('add_hospital'))

        hospital = Hospital(name=name, total_beds=total_beds, district_id=district_id)
        db.session.add(hospital)
        db.session.commit()

        flash(f'Hospital {name} added successfully!')
        return redirect(url_for('dashboard'))

    districts = District.query.all()
    return render_template('add_hospital.html', districts=districts)

@app.route('/add_district', methods=['GET', 'POST'])
def add_district():
    if session.get('role') != 'admin':
        flash('Only administrators can add districts.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']

        if not name:
            flash('District name is required!')
            return redirect(url_for('add_district'))

        district = District(name=name)
        db.session.add(district)
        db.session.commit()

        flash(f'District {name} added successfully!')
        return redirect(url_for('dashboard'))

    return render_template('add_district.html')

@app.route('/edit_hospital/<int:hospital_id>', methods=['GET', 'POST'])
def edit_hospital(hospital_id):
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        flash(f'Hospital with ID {hospital_id} not found!', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        hospital.name = request.form['name']
        hospital.total_beds = request.form['total_beds']
        db.session.commit()
        flash(f'Hospital {hospital.name} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_hospital.html', hospital=hospital.to_dict())

@app.route('/delete_hospital/<int:hospital_id>', methods=['POST'])
def delete_hospital(hospital_id):
    hospital = Hospital.query.get(hospital_id)
    if not hospital:
        flash(f'Hospital with ID {hospital_id} not found!', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(hospital)
    db.session.commit()
    flash(f'Hospital {hospital.name} deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit_district/<int:district_id>', methods=['GET', 'POST'])
def edit_district(district_id):
    district = District.query.get(district_id)
    if not district:
        flash(f'District with ID {district_id} not found!', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        district.name = request.form['name']
        db.session.commit()
        flash(f'District {district.name} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_district.html', district=district.to_dict())

@app.route('/delete_district/<int:district_id>', methods=['POST'])
def delete_district(district_id):
    district = District.query.get(district_id)
    if not district:
        flash(f'District with ID {district_id} not found!', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(district)
    db.session.commit()
    flash(f'District {district.name} deleted successfully!', 'success')
    return redirect(url_for('dashboard'))
# Patient registration route
@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if session.get('role') != 'admin':
        flash('You must be an admin to register patients.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = {
            'username': request.form['username'],
            'name': request.form['name'],
            'age': request.form['age'],
            'gender': request.form['gender'],
            'note': request.form.get('note', ''),
            'covid': request.form.get('covid', 'False') == 'True',
            'status': request.form.get('status', 'in wait'),
            'hospital_id': request.form.get('hospital_id'),
            'district_id': request.form['district_id']
        }
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if password != repeat_password:
            flash('Passwords do not match!')
            return redirect(url_for('register_patient'))

        user = User(
            username=data['username'],
            password=generate_password_hash(password),
            role='patient'
        )
        patient = Patient.to_db(data)

        db.session.add(user)
        db.session.add(patient)
        db.session.commit()

        flash(f'Patient {data["name"]} registered successfully!')
        return redirect(url_for('dashboard'))
    return render_template('register_patient.html')

# Add doctor route
@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if session.get('role') not in ['admin', 'assistant']:
        flash('You must be an admin or assistant to add doctors.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = {
            'username': request.form['username'],
            'name': request.form['name'],
            'specialty': request.form['specialty'],
            'password': request.form['password'],
            'repeat_password': request.form['repeat_password'],
            'note': request.form.get('note', ''),
            'hospital_id': request.form.get('hospital_id'),
            'district_id': request.form.get('district_id')
        }

        if not all([data['username'], data['name'], data['specialty'], data['password'], data['repeat_password'], data['hospital_id'], data['district_id']]):
            flash('All fields are required!')
            return redirect(url_for('add_doctor'))

        if data['password'] != data['repeat_password']:
            flash('Passwords do not match!')
            return redirect(url_for('add_doctor'))

        if User.query.filter_by(username=data['username']).first():
            flash('Username already exists.')
            return redirect(url_for('add_doctor'))

        user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            role='doctor'
        )
        doctor = Doctor(
            username=data['username'],  # Add username to Doctor model
            name=data['name'],
            specialty=data['specialty'],
            note=data['note'],
            hospital_id=data['hospital_id'],
            district_id=data['district_id']
        )

        db.session.add(user)
        db.session.add(doctor)
        db.session.commit()

        flash(f'Doctor {data["name"]} added successfully!')
        return redirect(url_for('assistant_dashboard'))

    hospitals = Hospital.query.all()
    districts = District.query.all()
    return render_template('add_doctor.html', hospitals=hospitals, districts=districts)

@app.route('/edit_doctor/<username>', methods=['GET', 'POST'])
def edit_doctor(username):
    # Fetch the doctor from the database using the username
    doctor = Doctor.query.filter_by(username=username).first()
    if not doctor:
        flash(f'Doctor with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the doctor's details from the form
        doctor.name = request.form['name']
        doctor.specialty = request.form['specialty']
        doctor.note = request.form.get('note', doctor.note)
        db.session.commit()
        flash(f'Doctor {doctor.name} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # If the request method is GET, render the form to edit the doctor details
    return render_template('edit_doctor.html', doctor=doctor.to_dict())

@app.route('/delete_doctor/<username>', methods=['POST'])
def delete_doctor(username):
    # Check if the doctor exists in the database
    doctor = Doctor.query.filter_by(username=username).first()
    if not doctor:
        flash(f'Doctor with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the doctor from the database
    db.session.delete(doctor)
    db.session.commit()
    flash(f'Doctor {doctor.name} deleted successfully!', 'success')

    # Redirect to the dashboard
    return redirect(url_for('dashboard'))
@app.route('/edit_patient/<username>', methods=['GET', 'POST'])
def edit_patient(username):
    # Check if the current user is an admin, nurse or doctor
    if session.get('role') not in ['admin', 'nurse', 'doctor']:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))

    # Fetch the patient from the database using the username
    patient = Patient.query.filter_by(username=username).first()
    if not patient:
        flash(f'Patient with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Fetch all hospitals
    hospitals = {hospital.name: hospital.to_dict() for hospital in Hospital.query.all()}

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the patient's details from the form
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.note = request.form['note']
        patient.status = request.form['status']
        
        # Update COVID status only if the field is provided and is "True" or "False"
        if 'covid' in request.form:
            covid_status = request.form['covid']
            if covid_status.lower() in ['true', 'false']:
                patient.covid = covid_status.lower() == 'true'
            else:
                flash(f'Invalid COVID status for patient {username}. It should be "True" or "False".', 'error')
                return redirect(url_for('edit_patient', username=username))

        db.session.commit()
        flash(f'Patient {patient.name} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # If the request method is GET, render the form to edit the patient details
    return render_template('edit_patient.html', patient=patient.to_dict(), hospitals=hospitals)

@app.route('/delete_patient/<username>', methods=['POST'])
def delete_patient(username):
    # Check if the patient exists in the database
    patient = Patient.query.filter_by(username=username).first()
    if not patient:
        flash(f'Patient with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the patient from the database
    db.session.delete(patient)
    db.session.commit()
    flash(f'Patient {patient.name} deleted successfully!', 'success')

    # Redirect back to the dashboard
    return redirect(url_for('dashboard'))

# Route to manage nurses (admin-only)
# Add Nurse Route
@app.route('/add_nurse', methods=['GET', 'POST'])
def add_nurse():
    if session.get('role') not in ['admin', 'assistant']:
        flash('You must be an admin or assistant to add head nurses.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = {
            'username': request.form['username'],
            'name': request.form['name'],
            'note': request.form.get('note', ''),
            'hospital_id': request.form['hospital_id'],
            'district_id': request.form['district_id']
        }
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if not all([data['username'], data['name'], data['hospital_id'], data['district_id'], password, repeat_password]):
            flash('All fields are required!')
            return redirect(url_for('add_nurse'))

        if password != repeat_password:
            flash('Passwords do not match!')
            return redirect(url_for('add_nurse'))

        if User.query.filter_by(username=data['username']).first():
            flash('Username already exists.')
            return redirect(url_for('add_nurse'))

        user = User(
            username=data['username'],
            password=generate_password_hash(password),
            role='head_nurse'
        )
        nurse = Nurse.to_db(data)

        db.session.add(user)
        db.session.add(nurse)
        db.session.commit()

        flash(f'Head Nurse {data["name"]} added successfully!')
        return redirect(url_for('dashboard'))

    hospitals = Hospital.query.all()
    districts = District.query.all()
    return render_template('add_head_nurse.html', hospitals=hospitals, districts=districts)

@app.route('/delete_nurse/<username>', methods=['POST'])
def delete_nurse(username):
    # Check if the nurse exists in the database
    nurse = Nurse.query.filter_by(username=username).first()
    if not nurse:
        flash(f'Nurse with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the nurse from the database
    db.session.delete(nurse)
    db.session.commit()
    flash(f'Nurse {nurse.name} deleted successfully!', 'success')

    # Redirect back to the dashboard
    return redirect(url_for('dashboard'))

# Route to manage nurses (admin-only)
@app.route('/manage_nurses', methods=['GET', 'POST'])
def manage_nurses():
    if session.get('role') != 'admin':
        flash('Only administrators can access this page.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data for new nurse
        data = {
            'username': request.form.get('username'),
            'name': request.form.get('name'),
            'note': request.form.get('note', ''),
            'hospital_id': request.form.get('hospital_id'),
            'district_id': request.form.get('district_id')
        }
        password = request.form.get('password')
        repeat_password = request.form.get('repeat_password')

        # Validate input
        if not all([data['username'], data['name'], data['hospital_id'], data['district_id'], password, repeat_password]):
            flash('All fields are required!')
            return redirect(url_for('manage_nurses'))

        if password != repeat_password:
            flash('Passwords do not match!')
            return redirect(url_for('manage_nurses'))

        if User.query.filter_by(username=data['username']).first():
            flash(f'Username {data["username"]} already exists!')
            return redirect(url_for('manage_nurses'))

        # Add the new nurse to the database
        user = User(
            username=data['username'],
            password=generate_password_hash(password),
            role='head_nurse'
        )
        nurse = Nurse.to_db(data)

        db.session.add(user)
        db.session.add(nurse)
        db.session.commit()

        flash(f'Head Nurse {data["name"]} added successfully!')
        return redirect(url_for('manage_nurses'))

    # For GET request, just render the page with existing nurses
    nurses_data = {nurse.id: nurse.to_dict() for nurse in Nurse.query.all()}
    hospitals_data = {hospital.id: hospital.to_dict() for hospital in Hospital.query.all()}
    districts_data = {district.id: district.to_dict() for district in District.query.all()}
    return render_template('manage_nurses.html', nurses=nurses_data, hospitals=hospitals_data, districts=districts_data)

@app.route('/edit_nurse/<username>', methods=['GET', 'POST'])
def edit_nurse(username):
    # Fetch the nurse from the database using the username
    nurse = Nurse.query.filter_by(username=username).first()
    if not nurse:
        flash(f'Nurse with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the nurse's details from the form
        nurse.name = request.form['name']
        nurse.note = request.form.get('note', nurse.note)
        db.session.commit()
        flash(f'Nurse {nurse.name} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # If the request method is GET, render the form to edit the nurse details
    return render_template('edit_nurse.html', nurse=nurse.to_dict())

@app.route('/manage_doctors', methods=['GET', 'POST'])
def manage_doctors():
    if session.get('role') != 'admin':
        flash('Only administrators can access this page.')
        return redirect(url_for('dashboard'))

    # Handle deleting a doctor
    if request.method == 'POST' and 'delete_doctor' in request.form:
        username = request.form.get('username')
        if username:
            doctor = Doctor.query.filter_by(username=username).first()
            if doctor:
                db.session.delete(doctor)
                db.session.commit()
                flash('Doctor deleted successfully.')
            else:
                flash('Error deleting doctor.')

    doctors_data = {doctor.username: doctor.to_dict() for doctor in Doctor.query.all()}
    return render_template('manage_doctors.html', doctors=doctors_data)

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session.get('role') != 'admin':
        flash('Only administrators can manage users.')
        return redirect(url_for('dashboard'))

    # Fetch all user data (patients, doctors, nurses, etc.)
    users_data = {
        'patients': {patient.username: patient.to_dict() for patient in Patient.query.all()},
        'doctors': {doctor.username: doctor.to_dict() for doctor in Doctor.query.all()},
        'nurses': {nurse.username: nurse.to_dict() for nurse in Nurse.query.all()}
    }

    if request.method == 'POST':
        # Handle the edit user functionality
        user_type = request.form.get('user_type')  # E.g., 'patients', 'doctors', 'nurses'
        username = request.form.get('username')  # Username of the user to edit
        field = request.form.get('field')  # Field to edit (e.g., 'name', 'specialty')
        new_value = request.form.get('new_value')  # New value to update

        # Validate inputs
        if not all([user_type, username, field, new_value]):
            flash("Incomplete data provided for editing.")
            return redirect(url_for('manage_users'))

        # Update the corresponding user's data
        if user_type == 'patients':
            user = Patient.query.filter_by(username=username).first()
        elif user_type == 'doctors':
            user = Doctor.query.filter_by(username=username).first()
        elif user_type == 'nurses':
            user = Nurse.query.filter_by(username=username).first()
        else:
            user = None

        if user:
            setattr(user, field, new_value)
            db.session.commit()
            flash(f'{user_type.capitalize()} {username} updated successfully!')
        else:
            flash(f'{user_type.capitalize()} {username} not found or cannot be edited.')

    return render_template('manage_users.html', users=users_data)

@app.route('/schedule_appointment', methods=['GET', 'POST'])
def schedule_appointment():
    # Ensure that the logged-in user is a patient
    if session.get('role') != 'patient':
        flash('Only patients can schedule appointments.')
        return redirect(url_for('dashboard'))

    patient_username = session.get('username')  # Get logged-in patient's username

    # Check if the patient exists in the database
    patient = Patient.query.filter_by(username=patient_username).first()
    if not patient:
        flash('Patient not found in the system.')
        return redirect(url_for('dashboard'))

    # Handle POST request (appointment creation)
    if request.method == 'POST':
        doctor_username = request.form['doctor']
        date = request.form['date']
        time = request.form['time']

        # Validate doctor existence
        doctor = Doctor.query.filter_by(username=doctor_username).first()
        if not doctor:
            flash('Doctor not found!')
            return redirect(url_for('schedule_appointment'))

        # Check for conflicting appointment (same doctor, same date, same time)
        conflicting_appointment = Appointment.query.filter_by(doctor_id=doctor.id, date=date, time=time).first()
        if conflicting_appointment:
            flash(f'The doctor is already booked at {time} on {date}. Please choose another time.')
            return redirect(url_for('schedule_appointment'))

        # Create the appointment
        appointment_data = {
            'patient_id': patient.id,
            'doctor_id': doctor.id,
            'date': date,
            'time': time
        }
        appointment = Appointment.to_db(appointment_data)

        # Store the appointment in the database
        db.session.add(appointment)
        db.session.commit()

        # Flash a success message
        flash(f'Appointment successfully scheduled with Dr. {doctor.name} on {date} at {time}')
        
        # Redirect back to the dashboard
        return redirect(url_for('dashboard'))

    # If it's a GET request, render the scheduling form with doctor options
    doctors = {doctor.username: doctor.to_dict() for doctor in Doctor.query.all()}
    return render_template('schedule_appointment.html', doctors=doctors, patient=patient.to_dict())

@app.route('/view_appointment/<int:appointment_id>', methods=['GET'])
def view_appointment(appointment_id):
    # Get the appointment from the database
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        flash(f'Appointment {appointment_id} not found!')
        return redirect(url_for('dashboard'))

    # Get the patient and doctor information
    patient = Patient.query.get(appointment.patient_id)
    doctor = Doctor.query.get(appointment.doctor_id)

    if not patient or not doctor:
        flash('Invalid patient or doctor details!')
        return redirect(url_for('dashboard'))

    # Render the view_appointment.html template with appointment details
    return render_template('view_appointment.html', appointment=appointment.to_dict(), patient=patient.to_dict(), doctor=doctor.to_dict())

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    # Get the role of the logged-in user
    username = session.get('username')
    role = session.get('role')

    # Fetch the appointment by ID
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        flash('Appointment not found!')
        return redirect(url_for('dashboard'))

    # Allow nurses or the patient associated with the appointment
    if role == 'patient':
        if appointment.patient_id != Patient.query.filter_by(username=username).first().id:
            flash('Unauthorized access to this appointment.')
            return redirect(url_for('dashboard'))
    elif role == 'head_nurse':
        # Nurses can edit any appointment, no extra checks
        return render_template('edit_appointment.html', appointment=appointment.to_dict())
    else:
        flash('Unauthorized role!')
        return redirect(url_for('dashboard'))

    # Handle POST request to update appointment details
    if request.method == 'POST':
        # Get new date and time from the form
        new_date = request.form.get('date')
        new_time = request.form.get('time')

        # Validate input
        if not new_date or not new_time:
            flash('Both date and time are required!', 'error')
            return render_template('edit_appointment.html', appointment=appointment.to_dict())

        # Update the appointment
        appointment.date = datetime.strptime(new_date, '%Y-%m-%d').date()
        appointment.time = datetime.strptime(new_time, '%H:%M:%S').time()
        db.session.commit()

        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Render the edit form for GET request
    return render_template('edit_appointment.html', appointment=appointment.to_dict())

@app.route('/finish_appointment/<int:appointment_id>', methods=['POST'])
def finish_appointment(appointment_id):
    # Ensure that the logged-in user is a doctor
    username = session.get('username')
    role = session.get('role')
    if role != 'doctor':
        flash('Only doctors can finish appointments.')
        return redirect(url_for('dashboard'))

    # Check if the appointment exists
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        flash(f'Appointment with ID {appointment_id} not found!')
        return redirect(url_for('dashboard'))

    # Check if the doctor is handling this appointment
    if appointment.doctor_id != Doctor.query.filter_by(username=username).first().id:
        flash('You are not authorized to finish this appointment.')
        return redirect(url_for('dashboard'))

    # Remove the appointment from the database
    db.session.delete(appointment)
    db.session.commit()

    flash(f'Appointment with {Patient.query.get(appointment.patient_id).name} on {appointment.date} at {appointment.time} has been finished.')
    return redirect(url_for('dashboard'))

@app.route('/view_bed', methods=['GET'])
def view_bed():
    username = session.get('username')
    role = session.get('role')

    if not username or (role != 'patient' and role != 'head_nurse'):
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))

    assigned_bed = None
    assigned_hospital = None

    # Search for patient's bed assignment
    patient = Patient.query.filter_by(username=username).first()
    if patient and patient.hospital_id:
        hospital = Hospital.query.get(patient.hospital_id)
        assigned_hospital = hospital.name
        assigned_bed = hospital.beds.index(patient.id) + 1  # 1-based index

    if assigned_bed:
        return render_template('view_bed.html', bed_number=assigned_bed, hospital=assigned_hospital)
    else:
        flash("You are not assigned to any bed.")
        return redirect(url_for('dashboard'))

@app.route('/assign_bed', methods=['GET', 'POST'])
def assign_bed():
    username = session.get('username')
    role = session.get('role')

    # Ensure the user is logged in and is a head nurse, doctor, or assistant
    if not username or role not in ('head_nurse', 'doctor', 'assistant'):
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Get patient username and hospital from the form
        patient_username = request.form.get('patient_username')
        hospital_id = request.form.get('hospital_id')

        # Validate patient username
        patient = Patient.query.filter_by(username=patient_username).first()
        if not patient:
            flash("Invalid patient username.")
            return redirect(url_for('assign_bed'))

        # Check if the patient has COVID
        if not patient.covid:
            flash(f"Cannot assign bed to {patient_username}: COVID status is False.")
            return redirect(url_for('assign_bed'))

        # Validate hospital ID
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            flash("Invalid hospital ID.")
            return redirect(url_for('assign_bed'))

        # Try to assign the first available bed
        try:
            bed_index = hospital.beds.index(None)  # Find the first unoccupied bed
            hospital.beds[bed_index] = patient.id  # Assign the bed to the patient
            db.session.commit()
            flash(f"Bed {bed_index + 1} assigned to {patient_username} in {hospital.name}.")
        except ValueError:  # If no beds are available
            flash(f"No available beds in {hospital.name}.")
            return redirect(url_for('assign_bed'))

        # Redirect back to the dashboard after successful assignment
        return redirect(url_for('dashboard'))

    hospitals = {hospital.id: hospital.to_dict() for hospital in Hospital.query.all()}
    patients = {patient.username: patient.to_dict() for patient in Patient.query.filter_by(covid=True).all()}
    return render_template('assign_bed.html', hospitals=hospitals, patients=patients)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('username'):
        flash('You are already logged in.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = {
            'username': request.form['username'],
            'password': request.form['password'],
            'name': request.form['name'],
            'age': request.form['age'],
            'gender': request.form['gender'],
            'district_id': request.form['district'],
            'hospital_id': request.form.get('hospital')
        }
        repeat_password = request.form['repeat_password']

        if User.query.filter_by(username=data['username']).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        if data['password'] != repeat_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            role='patient'
        )
        patient = Patient.to_db(data)

        db.session.add(user)
        db.session.add(patient)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    districts = {district.id: district.to_dict() for district in District.query.all()}
    return render_template('register.html', districts=districts)

@app.route('/assistant_dashboard')
def assistant_dashboard():
    if session.get('role') != 'assistant':
        flash('Unauthorized access!')
        return redirect(url_for('dashboard'))
    return render_template('dashboard_assistant.html')

@app.route('/delete_assistant/<username>', methods=['POST'])
def delete_assistant(username):
    # Check if the assistant exists in the database
    assistant = Assistant.query.filter_by(username=username).first()
    if not assistant:
        flash(f'Assistant with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the assistant from the database
    db.session.delete(assistant)
    db.session.commit()
    flash(f'Assistant {assistant.name} deleted successfully!', 'success')

    # Redirect back to the dashboard
    return redirect(url_for('dashboard'))

@app.route('/manage_assistants', methods=['GET', 'POST'])
def manage_assistants():
    if session.get('role') != 'admin':
        flash('Only administrators can access this page.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data for new assistant
        hospital_id = request.form.get('hospital_id')
        if hospital_id is None:
            flash('Hospital ID is required!')
            return redirect(url_for('manage_assistants'))

        data = {
            'username': request.form.get('username'),
            'name': request.form.get('name'),
            'hospital_id': int(hospital_id),
            'password': request.form.get('password'),
            'repeat_password': request.form.get('repeat_password')
        }

        # Validate input
        if not all([data['username'], data['name'], data['hospital_id'], data['password'], data['repeat_password']]):
            flash('All fields are required!')
            return redirect(url_for('manage_assistants'))

        if data['password'] != data['repeat_password']:
            flash('Passwords do not match!')
            return redirect(url_for('manage_assistants'))

        if User.query.filter_by(username=data['username']).first():
            flash(f'Username {data["username"]} already exists!')
            return redirect(url_for('manage_assistants'))

        # Add the new assistant to the database
        user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            role='assistant'
        )
        assistant = Assistant(
            username=data['username'],
            name=data['name'],
            hospital_id=data['hospital_id']
        )

        db.session.add(user)
        db.session.add(assistant)
        db.session.commit()

        flash(f'Assistant {data["name"]} added successfully!')
        return redirect(url_for('manage_assistants'))

    # For GET request, just render the page with existing assistants
    assistants_data = {assistant.username: assistant.to_dict() for assistant in Assistant.query.all()}
    hospitals_data = {hospital.id: hospital.to_dict() for hospital in Hospital.query.all()}
    return render_template('manage_assistants.html', assistants=assistants_data, hospitals=hospitals_data)



# Run the app
if __name__ == '__main__':
    app.run(debug=True)
