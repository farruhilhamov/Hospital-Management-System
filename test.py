from flask import Flask, jsonify
from models import db, User, District, Hospital, Assistant, Doctor, Nurse, Patient, Appointment

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create all tables if they do not exist
with app.app_context():
    db.create_all()

@app.route('/all_data', methods=['GET'])
def get_all_data():
    """Fetch all data from the database and return as JSON."""
    data = {
        "users": [user.to_dict() for user in User.query.all()],
        "districts": [district.to_dict() for district in District.query.all()],
        "hospitals": [hospital.to_dict() for hospital in Hospital.query.all()],
        "assistants": [assistant.to_dict() for assistant in Assistant.query.all()],
        "doctors": [doctor.to_dict() for doctor in Doctor.query.all()],
        "nurses": [nurse.to_dict() for nurse in Nurse.query.all()],
        "patients": [patient.to_dict() for patient in Patient.query.all()],
        "appointments": [appointment.to_dict() for appointment in Appointment.query.all()],
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
