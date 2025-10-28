from database import db

class Admin(db.Model):
    __tablename__ = "admin"

    username=db.Column(db.String(64), primary_key=True)
    password=db.Column(db.String(64))

class Doctor(db.Model):
    __tablename__="doctor"

    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    username=db.Column(db.String(64), unique=True, nullable=False)
    password=db.Column(db.String(64), nullable=False)

    appointments=db.relationship("Appointment", back_populates="doctor")
    departments=db.relationship("Department", secondary="department_doctor", back_populates="doctors")

class Patient(db.Model):
    __tablename__="patient"

    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    username=db.Column(db.String(64), unique=True, nullable=False)
    password=db.Column(db.String(64), nullable=False)

    appointments=db.relationship("Appointment", back_populates="patient")

class Appointment(db.Model):
    __tablename__="appointment"

    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id=db.Column(db.Integer, db.ForeignKey("patient.id"))
    doctor_id=db.Column(db.Integer, db.ForeignKey("doctor.id"))
    date=db.Column(db.Date, nullable=False)
    time=db.Column(db.Time, nullable=False)
    status=db.Column(db.Enum('Booked','Completed','Cancelled'), nullable=False)
    
    patient=db.relationship("Patient", back_populates="appointments")
    doctor=db.relationship("Doctor", back_populates="appointments")
    treatments=db.relationship("Treatment", back_populates="appointment")

class Treatment(db.Model):
    __tablename__="treatment"

    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_id=db.Column(db.Integer, db.ForeignKey("appointment.id"))
    diagnosis=db.Column(db.String(2048))
    prescription=db.Column(db.String(2048))
    notes=db.Column(db.String(2048))
    
    appointment=db.relationship("Appointment", back_populates="treatments")

class Department(db.Model):
    __tablename__="department"

    id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_name=db.Column(db.String(256), nullable=False)
    description=db.Column(db.String(1024))

    doctors=db.relationship("Doctor", secondary="department_doctor", back_populates="departments")

class DepartmentDoctor(db.Model):
    __tablename__="department_doctor"

    department_id=db.Column(db.Integer, db.ForeignKey("department.id"), primary_key=True)
    doctor_id=db.Column(db.Integer, db.ForeignKey("doctor.id"), primary_key=True)
