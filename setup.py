import psycopg2
from psycopg2 import sql

def create_tables():
    commands = (
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            specialty VARCHAR(255),
            hospital_id INTEGER,
            FOREIGN KEY (hospital_id)
                REFERENCES hospitals (hospital_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS nurses (
            nurse_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            note TEXT,
            hospital_id INTEGER,
            FOREIGN KEY (hospital_id)
                REFERENCES hospitals (hospital_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            age INTEGER,
            gender VARCHAR(50),
            note TEXT,
            covid BOOLEAN,
            hospital_id INTEGER,
            district VARCHAR(255),
            FOREIGN KEY (hospital_id)
                REFERENCES hospitals (hospital_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id SERIAL PRIMARY KEY,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            status VARCHAR(50) NOT NULL,
            FOREIGN KEY (patient_id)
                REFERENCES patients (patient_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (doctor_id)
                REFERENCES doctors (doctor_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            total_beds INTEGER NOT NULL,
            beds INTEGER[]
        )
        """
    )
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="yourdbname", user="yourusername", password="yourpassword", host="yourhost", port="yourport"
        )
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    create_tables()