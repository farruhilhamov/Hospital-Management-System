from werkzeug.security import generate_password_hash
from datetime import datetime
from models import db, User, District, Hospital, Assistant, Doctor, Nurse, Patient, Appointment
from test import app  # Assuming your Flask app is in app.py

# Data structures
users = {
    "admin": {"password": generate_password_hash("admin123"), "role": "admin"},
    "doctor1": {"password": generate_password_hash("doctor123"), "role": "doctor"},
    "patient1": {"password": generate_password_hash("patient123"), "role": "patient"},
    "headnurse1": {"password": generate_password_hash("nurse123"), "role": "head_nurse"},
    "assistant1": {"password": generate_password_hash("assistant123"), "role": "assistant"}
}

districts = {
    "district1": {
        "name": "District 1",
        "hospitals": ["hospital1"]
    },
    "district2": {
        "name": "District 2",
        "hospitals": ["hospital2"]
    }
}

assistants = {
    "assistant1": {
        "name": "Assistant One",
        "hospital": "hospital1"
    }
}

doctors = {
    "doctor1": {
        "name": "Smith",
        "specialty": "Cardiology",
        "note": "Senior Cardiologist.",
        "hospital": "hospital1",
        "district": "district1"
    }
}

nurses = {
    "headnurse1": {
        "name": "Nurse Jane",
        "note": "Head Nurse in the ICU.",
        "hospital": "hospital1",
        "district": "district1"
    }
}

patients = {
    "patient1": {
        "name": "John",
        "age": 30,
        "gender": "Male",
        "appointments": [1],
        "note": "Patient requires regular check-ups.",
        "covid": True,
        "hospital": None,
        "district": "district1",
        "status": "in wait"
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

hospitals = {
    "hospital1": {
        "name": "Hospital 1",
        "total_beds": 20,
    },
    "hospital2": {
        "name": "Hospital 2",
        "total_beds": 10,
    }
}

# Populate database
with app.app_context():
    # Add users
    for username, data in users.items():
        user = User(username=username, password=data["password"], role=data["role"])
        db.session.add(user)

    # Add districts and hospitals
    district_map = {}
    hospital_map = {}
    for district_id, data in districts.items():
        district = District(name=data["name"])
        db.session.add(district)
        db.session.flush()
        district_map[district_id] = district.id

        for hospital_id in data["hospitals"]:
            hospital_data = hospitals[hospital_id]
            hospital = Hospital(name=hospital_data["name"], total_beds=hospital_data["total_beds"], district_id=district.id)
            db.session.add(hospital)
            db.session.flush()
            hospital_map[hospital_id] = hospital.id

    # Add assistants
    for username, data in assistants.items():
        assistant = Assistant(name=data["name"], hospital_id=hospital_map[data["hospital"]])
        db.session.add(assistant)

    # Add doctors
    doctor_map = {}
    for username, data in doctors.items():
        doctor = Doctor(name=data["name"], specialty=data["specialty"], note=data["note"],
                        hospital_id=hospital_map[data["hospital"]], district_id=district_map[data["district"]])
        db.session.add(doctor)
        db.session.flush()
        doctor_map[username] = doctor.id

    # Add nurses
    for username, data in nurses.items():
        nurse = Nurse(name=data["name"], note=data["note"],
                      hospital_id=hospital_map[data["hospital"]], district_id=district_map[data["district"]])
        db.session.add(nurse)

    # Add patients
    patient_map = {}
    for username, data in patients.items():
        patient = Patient(name=data["name"], age=data["age"], gender=data["gender"], note=data["note"],
                          covid=data["covid"], status=data["status"], district_id=district_map[data["district"]])
        db.session.add(patient)
        db.session.flush()
        patient_map[username] = patient.id

    # Add appointments
    for appt_id, data in appointments.items():
        appointment = Appointment(patient_id=patient_map[data["patient"]],
                                  doctor_id=doctor_map[data["doctor"]],
                                  date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
                                  time=datetime.strptime(data["time"], "%H:%M").time(),
                                  status=data["status"])
        db.session.add(appointment)

    # Commit all changes
    db.session.commit()


