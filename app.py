from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Sample data
users = {
    "admin": {"password": generate_password_hash("admin123"), "role": "admin"},
    "doctor1": {"password": generate_password_hash("doctor123"), "role": "doctor"},
    "patient1": {"password": generate_password_hash("patient123"), "role": "patient"},
    "headnurse1":{"password": generate_password_hash("nurse123"), "role": "head_nurse"}
}

patients = {
    "patient1": {"name": "John", "age": 30, "gender": "Male", "appointments": []}
}

doctors = {
    "doctor1": {"name": "Dr. Smith", "specialty": "Cardiology"}
}

nurses = {username: user for username, user in users.items() if user.get('role') == 'head_nurse'} or {}

appointments = {}

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Home page route
@app.route('/')
def index():
    current_year = datetime.now().year
    username = session.get('username', None)
    role = session.get('role', None)
    return render_template('index.html', username=username, role=role, current_year=current_year)


@app.errorhandler(404)
def not_found(error):
    flash('The requested resource was not found.')
    return redirect(url_for('dashboard'))


@app.route('/user/<username>')
def profile(username):
    # Look up the patient by username in the patients dictionary
    user = patients.get(username)
    
    nurses = {username: user for username, user in users.items() if user.get('role') == 'head_nurse'} or {}


    # If the patient is not found, flash an error and redirect
    if not user:
        flash(f'User {username} not found!')
        return redirect(url_for('index'))

    # Render the profile page, passing the user (specific patient)
    return render_template('patient_profile.html', user=user, doctors=doctors,nurses=nurses)



# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists and the password is correct
        user_data = users.get(username)
        if user_data and check_password_hash(user_data['password'], password):
            # Set user session data
            session['username'] = username
            session['role'] = user_data['role']
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

    # Pass doctors and patients to all dashboards
    context = {
        'doctors': doctors,
        'patients': patients,
    }

    if role == 'admin':
        nurses = {username: user for username, user in users.items() if user.get('role') == 'head_nurse'}
        return render_template(
        'dashboard_admin.html',
        patients=patients,
        doctors=doctors,
        appointments=appointments,
        nurses=nurses
    )

    elif role == 'doctor':
        doctor = doctors.get(username)
        doctor_appointments = [appt for appt in appointments.values() if appt['doctor'] == username]
        return render_template('dashboard_doctor.html', **context, doctor=doctor, appointments=doctor_appointments)
    elif role == 'patient':
        patient = patients.get(username)
        patient_appointments = patient.get("appointments", [])
        return render_template('dashboard_patient.html', **context, patient=patient, appointments=patient_appointments)
    elif role == 'head_nurse':
        return render_template('dashboard_head_nurse.html', **context, appointments=appointments)

# Patient registration route
@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if session.get('role') != 'admin':
        flash('You must be an admin to register patients.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        patients[username] = {'name': name, 'age': age, 'gender': gender, 'appointments': []}
        flash(f'Patient {name} registered successfully!')
        return redirect(url_for('dashboard'))
    return render_template('register_patient.html')

# Add doctor route
@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if session.get('role') != 'admin':
        flash('You must be an admin to add doctors.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        specialty = request.form['specialty']
        doctors[username] = {'name': name, 'specialty': specialty}
        flash(f'Doctor {name} added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_doctor.html')

@app.route('/schedule_appointment', methods=['GET', 'POST'])
def schedule_appointment():
    # Ensure that the logged-in user is a patient
    if session.get('role') != 'patient':
        flash('Only patients can schedule appointments.')
        return redirect(url_for('dashboard'))

    patient_username = session.get('username')  # Get logged-in patient's username

    # Check if the patient exists in the patients dictionary
    if patient_username not in patients:
        flash('Patient not found in the system.')
        return redirect(url_for('dashboard'))

    # Handle POST request (appointment creation)
    if request.method == 'POST':
        doctor_username = request.form['doctor']
        date = request.form['date']
        time = request.form['time']

        # Validate doctor existence
        if doctor_username not in doctors:
            flash('Doctor not found!')
            return redirect(url_for('schedule_appointment'))

        # Check for conflicting appointment (same doctor, same date, same time)
        for appt in appointments.values():
            if appt['doctor'] == doctor_username and appt['date'] == date and appt['time'] == time:
                flash(f'The doctor is already booked at {time} on {date}. Please choose another time.')
                return redirect(url_for('schedule_appointment'))

        # Create the appointment
        appointment_id = len(appointments) + 1  # Generate a new appointment ID
        appointment = {
            'patient': patient_username,
            'doctor': doctor_username,
            'date': date,
            'time': time
        }

        # Store the appointment in the appointments dictionary
        appointments[appointment_id] = appointment

        # Optionally, add the appointment to the patient's list of appointments
        if 'appointments' not in patients[patient_username]:
            patients[patient_username]['appointments'] = []
        patients[patient_username]['appointments'].append(appointments[appointment_id])

        # Flash a success message
        flash(f'Appointment successfully scheduled with Dr. {doctors[doctor_username]["name"]} on {date} at {time}')
        
        # Redirect back to the dashboard
        return redirect(url_for('dashboard'))


    # If it's a GET request, render the scheduling form
    return render_template('schedule_appointment.html', doctors=doctors, patients=patients)

@app.route('/edit_doctor/<username>', methods=['GET', 'POST'])
def edit_doctor(username):
    doctor = doctors.get(username)
    if not doctor:
        flash(f'Doctor with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # You can update the doctor's information here
        doctor['name'] = request.form['name']
        doctor['specialty'] = request.form['specialty']
        flash(f'Doctor {doctor["name"]} updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/delete_doctor/<username>', methods=['POST'])
def delete_doctor(username):
    # Check if the doctor exists
    doctor = doctors.get(username)
    if not doctor:
        flash(f'Doctor with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the doctor from the dictionary
    del doctors[username]
    flash(f'Doctor {doctor["name"]} deleted successfully!', 'success')

    # Redirect to the dashboard
    return redirect(url_for('dashboard'))
@app.route('/edit_patient/<username>', methods=['GET', 'POST'])
def edit_patient(username):
    # Fetch the patient from the 'patients' dictionary using the username
    patient = patients.get(username)
    if not patient:
        flash(f'Patient with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the patient's details from the form
        patient['name'] = request.form['name']
        patient['age'] = request.form['age']
        patient['gender'] = request.form['gender']
        flash(f'Patient {patient["name"]} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # If the request method is GET, render the form to edit the patient details
    return render_template('edit_patient.html', patient=patient)

@app.route('/delete_patient/<username>', methods=['POST'])
def delete_patient(username):
    # Check if the patient exists in the dictionary
    patient = patients.get(username)
    if not patient:
        flash(f'Patient with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the patient from the 'patients' dictionary
    del patients[username]
    flash(f'Patient {patient["name"]} deleted successfully!', 'success')

    # Redirect back to the dashboard
    return redirect(url_for('dashboard'))

# Route to manage nurses (admin-only)
# Add Nurse Route
@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    if session.get('role') != 'admin':
        flash('Only administrators can manage nurses.')
        return redirect(url_for('dashboard'))

    username = request.form['username']
    name = request.form['name']
    specialty = request.form.get('specialty', '')
    password = request.form['password']

    # Check if the username already exists
    if username in users:
        flash(f'Username {username} already exists!')
        return redirect(url_for('manage_nurses'))

    # Add the new nurse
    users[username] = {"password": generate_password_hash(password), "role": "head_nurse"}
    nurses[username] = {"name": name, "specialty": specialty, "role": "head_nurse"}
    flash(f'Head Nurse {name} added successfully!')
    return redirect(url_for('manage_nurses'))

# Delete Nurse Route
@app.route('/delete_nurse/<username>', methods=['POST'])
def delete_nurse(username):
    if session.get('role') != 'admin':
        flash('Only administrators can manage nurses.')
        return redirect(url_for('dashboard'))

    # Check if the nurse exists
    if username not in nurses:
        flash(f'Head Nurse {username} not found!')
        return redirect(url_for('manage_nurses'))

    # Remove the nurse
    del nurses[username]
    del users[username]
    flash(f'Head Nurse {username} deleted successfully!')
    return redirect(url_for('manage_nurses'))

# Manage Nurses Page
@app.route('/manage_nurses')
def manage_nurses():
    if session.get('role') != 'admin':
        flash('Only administrators can access this page.')
        return redirect(url_for('dashboard'))
    
    return render_template('manage_nurses.html', nurses=nurses)

@app.route('/finish_appointment/<int:appointment_id>', methods=['POST'])
def finish_appointment(appointment_id):
    # Ensure that the logged-in user is a doctor
    username = session.get('username')
    role = session.get('role')
    if role != 'doctor':
        flash('Only doctors can finish appointments.')
        return redirect(url_for('dashboard'))

    # Check if the appointment exists
    appointment = appointments.get(appointment_id)
    if not appointment:
        flash(f'Appointment with ID {appointment_id} not found!')
        return redirect(url_for('dashboard'))

    # Check if the doctor is handling this appointment
    if appointment['doctor'] != username:
        flash('You are not authorized to finish this appointment.')
        return redirect(url_for('dashboard'))

    # Remove the appointment from the global appointments dictionary
    del appointments[appointment_id]

    # Remove the appointment from the patient's record
    patient_username = appointment['patient']
    if patient_username in patients:
        patient_appointments = patients[patient_username].get('appointments', [])
        patients[patient_username]['appointments'] = [
            appt for appt in patient_appointments if appt.get('id') != appointment_id
        ]

    flash(f'Appointment with {patients[patient_username]["name"]} on {appointment["date"]} at {appointment["time"]} has been finished.')
    return redirect(url_for('dashboard'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
