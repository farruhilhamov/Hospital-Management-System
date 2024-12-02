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
    "patient1": {"name": "John", "age": 30, "gender": "Male", "appointments": [1]}
}

doctors = {
    "doctor1": {"name": "Dr. Smith", "specialty": "Cardiology"}
}

nurses = {username: user for username, user in users.items() if user.get('role') == 'head_nurse'} or {}

appointments = {
    1: {
        "patient": "patient1",
        "doctor": "doctor1",
        "date": "2024-03-31",
        "time": "23:42",
        "status": "scheduled"
    }
}


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
    # Look up the user (could be a patient or doctor) by username
    user = patients.get(username) or doctors.get(username)

    # If the user is not found, flash an error and redirect
    if not user:
        flash(f'User {username} not found!')
        return redirect(url_for('index'))

    # Get the role of the logged-in user from the session
    role = session.get('role')

    # Admin can access all user data
    if role == 'admin':
        user_data = {
            "user": user,
            "appointments": [],
            "doctors": doctors,
            "nurses": nurses,
        }

    # Fetch patient-specific appointments
    if role in ['admin', 'doctor', 'head_nurse']:
        patient_appointments = user.get('appointments', [])
        user_data["appointments"] = [
            {
                "id": appt_id,
                **appointments.get(appt_id, {})
            }
            for appt_id in patient_appointments if appt_id in appointments
        ]

        return render_template('patient_profile.html', **user_data)

    # Doctors can view patient details and their appointments
    elif role == 'doctor' and username in patients:
        patient_appointments = user.get('appointments', [])
        detailed_appointments = [
            appointments.get(appt_id) for appt_id in patient_appointments if appt_id in appointments
        ]
        return render_template(
            'patient_profile.html',
            user=user,
            appointments=detailed_appointments,
            doctors=doctors,
        )

    # Head nurses can view patient details and appointments related to the user
    elif role == 'head_nurse' and username in patients:
        nurse_appointments = [appt for appt in appointments.values() if appt['patient'] == username]
        return render_template(
            'patient_profile.html',
            user=user,
            doctors=doctors,
            nurses=nurses,
            appointments=nurse_appointments,
        )

    # Handle unauthorized access
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

    # Base context to pass to templates
    context = {
        'doctors': doctors,
        'patients': patients,
    }

    # Admin dashboard
    if role == 'admin':
        nurses = {username: user for username, user in users.items() if user.get('role') == 'head_nurse'}
        context.update({'appointments': appointments, 'nurses': nurses})
        return render_template('dashboard_admin.html', **context,user=users)

    # Doctor dashboard
    elif role == 'doctor':
        doctor = doctors.get(username)
        if not doctor:
            flash('Doctor not found!')
            return redirect(url_for('index'))

        doctor_appointments = [appt for appt in appointments.values() if appt['doctor'] == username]
        context.update({'doctor': doctor, 'appointments': doctor_appointments})
        return render_template('dashboard_doctor.html', **context)

    # Patient dashboard
    elif role == 'patient':
        patient = patients.get(username)
        if not patient:
            flash('Patient not found!')
            return redirect(url_for('index'))

        # Fetch the appointment data for the patient
        patient_appointments = [appointments[appt_id] for appt_id in patient.get("appointments", []) if appt_id in appointments]
        context.update({'patient': patient, 'appointments': patient_appointments})
        return render_template('dashboard_patient.html', **context)

    # Head Nurse dashboard
    elif role == 'head_nurse':
        context.update({'appointments': appointments})
        return render_template('dashboard_head_nurse.html', **context)

    # Unauthorized role or access
    flash('Unauthorized access!')
    return redirect(url_for('index'))


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
        print(appointments)
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

# Route to manage nurses (admin-only)
@app.route('/manage_nurses', methods=['GET', 'POST'])
def manage_nurses():
    if session.get('role') != 'admin':
        flash('Only administrators can access this page.')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data for new nurse
        username = request.form.get('username')
        name = request.form.get('name')
        specialty = request.form.get('specialty')
        password = request.form.get('password')

        # Validate input
        if not username or not name or not specialty or not password:
            flash('All fields are required!')
            return redirect(url_for('manage_nurses'))

        # Check if the username exists
        if username in users:
            flash(f'Username {username} already exists!')
            return redirect(url_for('manage_nurses'))

        # Add the new nurse to the users and nurses dictionary
        users[username] = {"password": generate_password_hash(password), "role": "head_nurse"}
        nurses[username] = {"name": name, "specialty": specialty}
        flash(f'Head Nurse {name} added successfully!')
        return redirect(url_for('manage_nurses'))

    # For GET request, just render the page with existing nurses
    return render_template('manage_nurses.html', nurses=nurses)

@app.route('/edit_nurse/<username>', methods=['GET', 'POST'])
def edit_nurse(username):
    # Fetch the nurse from the 'nurses' dictionary
    nurse = nurses.get(username)
    if not nurse:
        flash(f'Head Nurse {username} not found!', 'error')
        return redirect(url_for('manage_nurses'))

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the nurse's details from the form
        nurse['name'] = request.form['name']
        nurse['specialty'] = request.form['specialty']
        flash(f'Head Nurse {nurse["name"]} updated successfully!', 'success')
        return redirect(url_for('manage_nurses'))

    # If the request method is GET, render the form to edit the nurse details
    return render_template('edit_nurse.html', nurse=nurse)


@app.route('/manage_doctors', methods=['GET', 'POST'])
def manage_doctors():
    if session.get('role') != 'admin':
        flash('Only administrators can access this page.')
        return redirect(url_for('dashboard'))

    # Handle deleting a doctor
    if request.method == 'POST' and 'delete_doctor' in request.form:
        username = request.form.get('username')
        if username:
            if delete_doctor(username):
                flash('Doctor deleted successfully.')
            else:
                flash('Error deleting doctor.')

    return render_template('manage_doctors.html', doctors=doctors)

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session.get('role') != 'admin':
        flash('Only administrators can manage users.')
        return redirect(url_for('dashboard'))

    # Fetch all user data (patients, doctors, nurses, etc.)
    users_data = {
        'patients': patients,
        'doctors': doctors,
        'nurses': nurses
    }

    if request.method == 'POST':
        # Handle the edit user functionality
        user_type = request.form.get('user_type')  # E.g., 'nurses'
        username = request.form.get('username')  # Username of the user to edit
        field = request.form.get('field')  # Field to edit (e.g., 'name', 'specialty')
        new_value = request.form.get('new_value')  # New value to update

        # Validate inputs
        if not all([user_type, username, field, new_value]):
            flash("Incomplete data provided for editing.")
            return redirect(url_for('manage_users'))

        # Update the corresponding user's data (only allows nurse edits here)
        if user_type == 'nurses' and username in nurses:
            nurses[username][field] = new_value
            flash(f'Nurse {username} updated successfully!')
        else:
            flash(f'{user_type.capitalize()} {username} not found or cannot be edited.')

    return render_template('manage_users.html', users=users_data)


@app.route('/view_appointment/<int:appointment_id>', methods=['GET'])
def view_appointment(appointment_id):
    # Get the appointment from the appointments dictionary
    appointment = appointments.get(appointment_id)

    if not appointment:
        flash(f'Appointment {appointment_id} not found!')
        return redirect(url_for('dashboard'))

    # Get the patient and doctor information
    patient = patients.get(appointment['patient'])
    doctor = doctors.get(appointment['doctor'])

    if not patient or not doctor:
        flash('Invalid patient or doctor details!')
        return redirect(url_for('dashboard'))

    # Render the view_appointment.html template with appointment details
    return render_template('view_appointment.html', appointment=appointment, patient=patient, doctor=doctor)


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
        if appointment_id in patient_appointments:
            patient_appointments.remove(appointment_id)
            patients[patient_username]['appointment']=patient_appointments

    flash(f'Appointment with {patients[patient_username]["name"]} on {appointment["date"]} at {appointment["time"]} has been finished.')
    return redirect(url_for('dashboard'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
