from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }

    @staticmethod
    def to_db(data):
        return User(
            username=data['username'],
            password=data['password'],
            role=data['role']
        )

class District(db.Model):
    __tablename__ = 'districts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hospitals = db.relationship('Hospital', backref='district', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hospitals': [hospital.to_dict() for hospital in self.hospitals]
        }

    @staticmethod
    def to_db(data):
        return District(
            name=data['name']
        )

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_beds = db.Column(db.Integer, nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'total_beds': self.total_beds,
            'district_id': self.district_id
        }

    @staticmethod
    def to_db(data):
        return Hospital(
            name=data['name'],
            total_beds=data['total_beds'],
            district_id=data['district_id']
        )

class Assistant(db.Model):
    __tablename__ = 'assistants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hospital_id': self.hospital_id
        }

    @staticmethod
    def to_db(data):
        return Assistant(
            name=data['name'],
            hospital_id=data['hospital_id']
        )

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text, nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'note': self.note,
            'hospital_id': self.hospital_id,
            'district_id': self.district_id
        }

    @staticmethod
    def to_db(data):
        return Doctor(
            name=data['name'],
            specialty=data['specialty'],
            note=data.get('note'),
            hospital_id=data['hospital_id'],
            district_id=data['district_id']
        )

class Nurse(db.Model):
    __tablename__ = 'nurses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text, nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'note': self.note,
            'hospital_id': self.hospital_id,
            'district_id': self.district_id
        }

    @staticmethod
    def to_db(data):
        return Nurse(
            name=data['name'],
            note=data.get('note'),
            hospital_id=data['hospital_id'],
            district_id=data['district_id']
        )

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    note = db.Column(db.Text, nullable=True)
    covid = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='in wait')
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'note': self.note,
            'covid': self.covid,
            'status': self.status,
            'hospital_id': self.hospital_id,
            'district_id': self.district_id
        }

    @staticmethod
    def to_db(data):
        return Patient(
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            note=data.get('note'),
            covid=data.get('covid', False),
            status=data.get('status', 'in wait'),
            hospital_id=data.get('hospital_id'),
            district_id=data['district_id']
        )

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), default='scheduled')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'time': self.time.strftime('%H:%M:%S'),
            'status': self.status
        }

    @staticmethod
    def to_db(data):
        return Appointment(
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            time=datetime.strptime(data['time'], '%H:%M:%S').time(),
            status=data.get('status', 'scheduled')
        )