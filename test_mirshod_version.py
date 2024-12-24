from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

"""
Mirshod says that he has errors in references that i had
"""

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plaintext_password):
        self.password_hash = generate_password_hash(password=plaintext_password)

    def check_password(self, attempted_password):
        return check_password_hash(self.password_hash, attempted_password)

    @staticmethod
    def get_by_username(username: str) -> 'User':
        return db.one_or_404(db.select(User).filter_by(username=username))

    @staticmethod
    def get_by_id(user_id) -> 'User':
        return db.get_or_404(User, user_id)

    @staticmethod
    def get_all() -> list['User']:
        return db.session.execute(db.select(User).order_by(User.username)).scalars()

    @staticmethod
    def add(**user_data) -> None:
        """
        @param user_data: dict = {
            username: str
            password: str (plaint text)
            role: str
        }
        """
        try:
            user = User(**user_data)
            db.session.add(user)

        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()

    @staticmethod
    def delete_by_id(user_id):
        try:
            db.session.delete(User.get_by_id(user_id))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()

    @staticmethod
    def delete_by_username(username):
        try:
            db.session.delete(User.get_by_username(username))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()


class District(db.Model):
    __tablename__ = 'districts'
    district_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

    @staticmethod
    def get(district_id: int) -> 'District':
        return db.get_or_404(District, district_id)

    @staticmethod
    def get_all() -> list['District']:
        return db.session.execute(db.select(District).order_by(District.name)).scalars()

    def get_hospitals(self) -> list[dict]:
        res = []
        district_hospitals = self.hospitals

        for hospital in district_hospitals:
            res.append(hospital.to_dict())

        return res

    def get_doctors(self) -> list[dict]:
        res = []
        district_doctors = self.doctors

        for doctor in district_doctors:
            res.append(doctor.to_dict())

        return res

    def to_dict(self) -> dict:
        return {
            "district_id": self.district_id,
            "district_name": self.name,
            "district_hospitals": self.get_hospitals(),
            "district_doctors": self.get_doctors(),
            "district_nurses": self.get_nurses(),
            "district_assistants": self.get_assistants()
        }

    @staticmethod
    def update_name(name: str, district_id: int):
        try:
            district = District.get(district_id)
            district.name = name
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()

    @staticmethod
    def delete(district_id: int) -> None:
        try:
            db.session.delete(District.get(district_id))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()


class Hospital(db.Model):
    __tablename__ = 'hospitals'
    hospital_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    total_beds = db.Column(db.Integer, nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.district_id', onupdate="CASCADE", ondelete="SET NULL"))

    district = db.relationship('District', db.backref('hospitals', lazy=True))
    beds = db.relationship('Bed', db.backref('hospital', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self) -> dict:
        return {
            "hospital_id": self.hospital_id,
            "hospital_name": self.name,
            "total_beds": self.total_beds,
            "district_id": self.district_id
        }

    @staticmethod
    def add(**hospital_data):
        """
        Adds hospital
        @param hospital_data: dict = {
            name: str,
            total_beds: int
            district_id: int
        }
        """
        try:
            hospital = Hospital(**hospital_data)
            db.session.add(hospital)
            db.session.commit()

            for i in range(hospital_data.get('total_beds')):
                db.session.add(Bed.add(i + 1, hospital.hospital_id))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()

    @staticmethod
    def get(hospital_id: int) -> 'Hospital':
        return db.get_or_404(District, hospital_id)

    @staticmethod
    def get_all() -> list['Hospital']:
        return db.session.execute(db.select(Hospital).order_by(Hospital.name)).scalars()

    @staticmethod
    def update_name(name: str, hospital_id: int):
        try:
            hospital = Hospital.get(hospital_id)
            hospital.name = name
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()

    @staticmethod
    def delete(hospital_id: int) -> None:
        try:
            db.session.delete(Hospital.get(hospital_id))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()


class Bed(db.Model):
    __tablename__ = 'beds'
    bed_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bed_number = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)

    # ForeignKey pointing to Patient
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id', ondelete='SET NULL'), unique=True, default=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.hospital_id', ondelete='SET NULL'))

    # One-to-one relationship with Patient
    patient = db.relationship('Patient', back_populates='bed')

    def to_dict(self) -> dict:
        return {
            "bed_id": self.bed_id,
            "bed_number": self.bed_number,
            "is_available": self.is_available,
            "hospital_id": self.hospital_id,
            "patient_id": self.patient_id
        }

    @staticmethod
    def add(bed_num: int, hospital_id: int):
        try:
            new_bed = Bed(bed_number=bed_num, hospital_id=hospital_id)
            db.session.add(new_bed)
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            db.session.close()

    def get_all_available_beds(self):
        pass

    def get_all_occupied_beds(self):
        pass

    def get_all(self):
        pass


class Doctor(db.Model):
    __tablename__ = 'doctors'
    doctor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(255))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.hospital_id', onupdate="CASCADE", ondelete="SET NULL"))

    hospital = db.relationship('Hospital', backref=db.backref('doctors', lazy=True))

    def to_dict(self):
        return {
            "doctor_id": self.doctor_id,
            "doctor_name": self.name,
            "doctor_specialty": self.specialty,
            "doctor_username": self.username,
            "hospital_id": self.hospital_id
        }


class Nurse(db.Model):
    __tablename__ = 'nurses'
    nurse_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    note = db.Column(db.Text)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.hospital_id', onupdate="CASCADE", ondelete="SET NULL"))

    hospital = db.relationship('Hospital', backref=db.backref('nurses', lazy=True))

    def to_dict(self):
        return {
            "nurse_id": self.nurse_id,
            "nurse_name": self.name,
            "nurse_username": self.username,
            "nurse_note": self.note,
            "hospital_id": self.hospital_id
        }


class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(50))
    note = db.Column(db.Text)
    covid = db.Column(db.Boolean)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.hospital_id', onupdate="CASCADE", ondelete="SET NULL"))

    # One-to-one relationship with Bed
    bed = db.relationship('Bed', back_populates='patient', uselist=False)

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "patient_name": self.name,
            "patient_username": self.username,
            "patient_age": self.age,
            "patient_gender": self.gender,
            "patient_note": self.note,
            "patient_covid": self.covid,
            "hospital_id": self.hospital_id
        }


class Assistant(db.Model):
    __tablename__ = 'assistants'
    assistant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.hospital_id', onupdate="CASCADE", ondelete="SET NULL"))

    hospital = db.relationship('Hospital', backref=db.backref('assistants', lazy=True))

    def to_dict(self):
        return {
            "assistant_id": self.assistant_id,
            "assistant_name": self.name,
            "hospital_id": self.hospital_id,
            "assistant_username": self.username,
        }


class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), nullable=False)

    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('appointments', lazy=True))


@app.get("/district")
def district_all():
    try:
        all_districts = District.get_all()
        res = []
        for district in all_districts:
            res.append(district.to_dict())
        return {
            'success': True,
            'districts': res
        }, 200
    except Exception as e:
        print(e)
        return {
            "success": False,
            "message": "Something went wrong"
        }, 500


@app.get("/district/<int:district_id>")
def district_get(district_id):
    try:
        district = District.get(district_id)
        return {
            'success': True,
            'district': district.to_dict()
        }, 200
    except Exception as e:
        print(e)
        return {
            "success": False,
            "message": "Something went wrong"
        }, 500

if __name__ == "__main__":
    app.run(debug=True)