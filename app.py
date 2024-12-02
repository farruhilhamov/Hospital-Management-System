from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

users = {
    "admin": {"password": generate_password_hash("admin123"), "role": "admin"},
    "doctor1": {"password": generate_password_hash("doctor123"), "role": "doctor"},
    "patient1": {"password": generate_password_hash("patient123"), "role": "patient"},
    "headnurse1": {"password": generate_password_hash("nurse123"), "role": "head_nurse"}
}

patients = {
    "patient1": {
        "name": "John",
        "age": 30,
        "gender": "Male",
        "appointments": [1],
        "note": "Patient requires regular check-ups.",
        "covid": False  # COVID status for patient
    }
}

doctors = {
    "doctor1": {
        "name": "Smith",
        "specialty": "Cardiology",
        "note": "Senior Cardiologist."
    }
}

nurses = {
    "headnurse1": {
        "name": "Nurse Jane",
        "note": "Head Nurse in the ICU."
    }
}

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


@app.route('/user/<username>', methods=['GET', 'POST'])
def profile(username):
    # Look up the user (could be a patient or doctor) by username
    user = patients.get(username) or doctors.get(username)

    # If the user is not found, flash an error and redirect
    if not user:
        flash(f'User {username} not found!')
        return redirect(url_for('index'))

    # Get the role of the logged-in user from the session
    role = session.get('role')

    # Admin can access all user data, including all appointments, notes, and COVID status
    if role == 'admin':
        user_data = {
            "user": user,
            "appointments": [],
            "doctors": doctors,
            "nurses": nurses,
            "notes": user.get('note', ''),
            "covid_status": user.get('covid', 'False'),
        }

        # Fetch all appointments if user is a patient
        if username in patients:
            patient_appointments = user.get('appointments', [])
            user_data["appointments"] = [
                {
                    "id": appt_id,
                    **appointments.get(appt_id, {})
                }
                for appt_id in patient_appointments if appt_id in appointments
            ]
        return render_template('patient_profile.html', **user_data)

    # Fetch patient-specific appointments, notes, and COVID status for doctors, head nurses, and admins
    if role in ['admin', 'doctor', 'head_nurse']:
        patient_appointments = user.get('appointments', [])
        user_data = {
            "user": user,
            "appointments": [
                {
                    "id": appt_id,
                    **appointments.get(appt_id, {})
                }
                for appt_id in patient_appointments if appt_id in appointments
            ],
            "notes": user.get('note', ''),
            "covid_status": user.get('covid', 'False'),
        }

        # Handle doctor POST request to update notes and covid status
        if request.method == 'POST' and role == 'doctor' and username in patients:
            note = request.form.get('note')
            covid_status = request.form.get('covid')

            # Debugging: Print the values received
            print(f"Received Note: {note}, Received COVID Status: {covid_status}")

            # Update the patient's notes and COVID status
            if note:
                user['note'] = note

            # Ensure covid_status is properly handled
            if covid_status in ['True', 'False']:
                # Debugging: Ensure the value of covid_status is correct
                print(f"Updated COVID Status: {covid_status}")
                user['covid'] = covid_status == 'True'  # Convert to boolean

            flash(f'Patient {username} updated successfully!', 'success')
            return redirect(url_for('profile', username=username))

        return render_template('patient_profile.html', **user_data)

    # Doctors can view patient details and their appointments if the user is a patient
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
            notes=user.get('note', ''),
            covid_status=user.get('covid', 'False'),
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
            notes=user.get('note', ''),
            covid_status=user.get('covid', 'False'),
        )

    # Handle unauthorized access
    flash('Unauthorized access to this profile.')
    return redirect(url_for('dashboard'))

# Function to handle viewing patient details (for doctors, nurses)
@app.route('/patient_details/<username>', methods=['GET'])
def patient_details(username):
    user = patients.get(username)

    if not user:
        flash('Patient not found!')
        return redirect(url_for('dashboard'))

    # Render patient profile for doctors, nurses, and admins
    role = session.get('role')
    if role in ['doctor', 'head_nurse', 'admin']:
        patient_appointments = user.get('appointments', [])
        patient_data = {
            "user": user,
            "appointments": [
                {
                    "id": appt_id,
                    **appointments.get(appt_id, {})
                }
                for appt_id in patient_appointments if appt_id in appointments
            ],
            "notes": user.get('note', ''),
            "covid_status": user.get('covid', 'False'),
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
        return render_template('dashboard_admin.html', **context, user=users)

    # Doctor dashboard
    elif role == 'doctor':
        doctor = doctors.get(username)
        if not doctor:
            flash('Doctor not found!')
            return redirect(url_for('index'))

        doctor_appointments = [
            appt for appt in appointments.values() if appt['doctor'] == username
        ]
        doctor_data = {
            'doctor': doctor,
            'appointments': doctor_appointments
        }
        # Adding patient details (COVID status, notes)
        for appt in doctor_appointments:
            patient = patients.get(appt['patient'])
            if patient:
                appt['patient_name'] = patient['name']
                appt['patient_covid'] = patient.get('covid', 'False')
                appt['patient_notes'] = patient.get('note', '')

        context.update(doctor_data)
        return render_template('dashboard_doctor.html', **context)

    # Patient dashboard
    elif role == 'patient':
        patient = patients.get(username)
        if not patient:
            flash('Patient not found!')
            return redirect(url_for('index'))

        # Fetch the appointment data for the patient
        patient_appointments = [
            appointments[appt_id] for appt_id in patient.get("appointments", []) if appt_id in appointments
        ]

        # Add relevant details for each appointment
        for appt in patient_appointments:
            doctor = doctors.get(appt['doctor'])
            if doctor:
                appt['doctor_name'] = doctor['name']
            appt['covid_status'] = patient.get('covid', 'False')
            appt['patient_notes'] = patient.get('note', '')

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

@app.route('/edit_doctor/<username>', methods=['GET', 'POST'])
def edit_doctor(username):
    # Fetch the doctor from the 'doctors' dictionary using the username
    doctor = doctors.get(username)
    if not doctor:
        flash(f'Doctor with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the doctor's details from the form
        doctor['name'] = request.form['name']
        doctor['specialty'] = request.form['specialty']
        flash(f'Doctor {doctor["name"]} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # If the request method is GET, render the form to edit the doctor details
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
    # Check if the current user is an admin or nurse
    if session.get('role') not in ['admin', 'nurse']:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))

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
        patient['note'] = request.form['note']
        
        # Update COVID status only if the field is provided and is "True" or "False"
        if 'covid' in request.form:
            covid_status = request.form['covid']
            if covid_status.lower() in ['true', 'false']:
                patient['covid'] = covid_status.lower() == 'true'
            else:
                flash(f'Invalid COVID status for patient {username}. It should be "True" or "False".', 'error')
                return redirect(url_for('edit_patient', username=username))

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
    # Check if the nurse exists in the dictionary
    nurse = nurses.get(username)
    if not nurse:
        flash(f'Nurse with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Delete the nurse from the 'nurses' dictionary
    del nurses[username]
    flash(f'Nurse {nurse["name"]} deleted successfully!', 'success')

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
    # Fetch the nurse from the 'nurses' dictionary using the username
    nurse = nurses.get(username)
    if not nurse:
        flash(f'Nurse with username {username} not found!', 'error')
        return redirect(url_for('dashboard'))

    # Handle the form submission (POST request)
    if request.method == 'POST':
        # Update the nurse's details from the form
        nurse['name'] = request.form['name']
        nurse['specialty'] = request.form['specialty']
        flash(f'Nurse {nurse["name"]} updated successfully!', 'success')
        return redirect(url_for('dashboard'))

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
        user_type = request.form.get('user_type')  # E.g., 'patients', 'doctors', 'nurses'
        username = request.form.get('username')  # Username of the user to edit
        field = request.form.get('field')  # Field to edit (e.g., 'name', 'specialty')
        new_value = request.form.get('new_value')  # New value to update

        # Validate inputs
        if not all([user_type, username, field, new_value]):
            flash("Incomplete data provided for editing.")
            return redirect(url_for('manage_users'))

        # Update the corresponding user's data
        if user_type == 'patients' and username in patients:
            if field in patients[username]:
                patients[username][field] = new_value
                flash(f'Patient {username} updated successfully!')
            else:
                flash(f'Field {field} not found for Patient {username}.')
        elif user_type == 'doctors' and username in doctors:
            if field in doctors[username]:
                doctors[username][field] = new_value
                flash(f'Doctor {username} updated successfully!')
            else:
                flash(f'Field {field} not found for Doctor {username}.')
        elif user_type == 'nurses' and username in nurses:
            if field in nurses[username]:
                nurses[username][field] = new_value
                flash(f'Nurse {username} updated successfully!')
            else:
                flash(f'Field {field} not found for Nurse {username}.')
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
        appointment_id = str(len(appointments) + 1)  # Use a unique string-based ID for appointments
        appointment = {
            'id': appointment_id,
            'patient': patient_username,
            'doctor': doctor_username,
            'date': date,
            'time': time
        }

        # Store the appointment in the appointments dictionary
        appointments[appointment_id] = appointment

        # Add the appointment to the patient's list of appointments
        if 'appointments' not in patients[patient_username]:
            patients[patient_username]['appointments'] = []
        patients[patient_username]['appointments'].append(appointment_id)

        # Flash a success message
        flash(f'Appointment successfully scheduled with Dr. {doctors[doctor_username]["name"]} on {date} at {time}')
        
        # Redirect back to the dashboard
        return redirect(url_for('dashboard'))

    # If it's a GET request, render the scheduling form with doctor options
    return render_template('schedule_appointment.html', doctors=doctors,patients=patients)

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

# Function to handle appointment editing for patients
@app.route('/edit_appointment/<appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    # Get the appointment data using the provided appointment_id
    appointment = appointments.get(appointment_id)
    
    if not appointment:
        flash('Appointment not found!')
        return redirect(url_for('dashboard'))

    # Fetch the patient data and verify the patient is logged in
    patient = patients.get(session.get('username'))
    if not patient or appointment['patient'] != patient['username']:
        flash('Unauthorized access to this appointment.')
        return redirect(url_for('dashboard'))

    # Handle POST request to update appointment details
    if request.method == 'POST':
        # Allow the patient to reschedule the appointment
        new_date = request.form['date']
        new_time = request.form['time']

        # Validate date and time fields (basic validation can be added)
        if not new_date or not new_time:
            flash('Both date and time are required!', 'error')
            return render_template('edit_appointment.html', appointment=appointment)

        # Update appointment details
        appointment['date'] = new_date
        appointment['time'] = new_time

        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Pass the appointment to the template for GET request
    return render_template('edit_appointment.html', appointment=appointment)


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
