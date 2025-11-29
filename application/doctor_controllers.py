from flask import current_app as app
from flask import render_template, redirect, request, session, abort
from .database import db
from .models import *

@app.route('/doctor/<username>',methods=["GET","POST"])
def doctor(username):
    if session.get('user_type')!='doctor':
        return abort(403)
    if request.method=="GET":
        doc=db.session.query(Doctor).filter_by(username=username).first()
        if not doc:
            return abort(404)
        if doc.blacklisted=='true':
            return render_template('blacklisted.html',role='doctor',person=doc)
        from datetime import datetime
        now=datetime.now()
        appointments=db.session.query(Appointment).filter_by(doctor_id=doc.id).order_by(Appointment.date,Appointment.time).all()
        appointments=[
            appointment for appointment in appointments
            if appointment.patient.username!="patient-dummy_001" and appointment.status=='Booked' and appointment.date>=now.date() and appointment.patient.blacklisted=='false'
        ]
        patients=[]
        for appointment in appointments:
            if appointment.patient.username not in patients:
                patients.append(appointment.patient.username)
        return render_template("doctor_dashboard.html",doc=doc,appointment_list=appointments,patient_list=patients)
    
@app.route('/doctor/update/availability/<doctor_id>',methods=['GET','POST'])
def update_doctor_availability(doctor_id):
    if session.get('user_type')!='doctor':
        return abort(403)
    doctor=db.session.query(Doctor).filter_by(id=doctor_id).first()
    if not doctor:
        return abort(404)
    if doctor.blacklisted=='true':
        return render_template('blacklisted.html',role='doctor',person=doctor)
    if request.method=='GET':
        appointments=db.session.query(Appointment).filter_by(doctor_id=doctor_id).order_by(Appointment.date,Appointment.time).all()
        from datetime import datetime,timedelta
        now=datetime.now()
        availability=dict()
        for i in range(7):
            date = now.date() + timedelta(days=i)
            date_str = date.strftime('%d-%m-%Y')
            availability[date_str] = [True, True]

        appointments = db.session.query(Appointment).filter_by(doctor_id=doctor_id).all()
        appointments=[
            appointment for appointment in appointments
            if (appointment.status=='Booked' and appointment.date>=now.date() and appointment.patient.blacklisted=='false')
        ]
        for appointment in appointments:
            appointment_date = appointment.date.strftime('%d-%m-%Y')
            if appointment_date in availability:
                if appointment.time == datetime.strptime('08:00:00', '%H:%M:%S').time():
                    availability[appointment_date][0] = False
                elif appointment.time == datetime.strptime('16:00:00', '%H:%M:%S').time():
                    availability[appointment_date][1] = False
        return render_template('doctor_availability.html',doctor=doctor,availability=availability)
    elif request.method=='POST':
        availability_data=request.form.to_dict(flat=False)
        from datetime import datetime
        for key,slots in availability_data.items():
            date=key.split('[')[1].split(']')[0]
            slot=key.split('[')[2].split(']')[0]
            date_obj=datetime.strptime(date,'%d-%m-%Y').date()
            if slot=='morning':
                print("here")
                morning_not_available='true' in slots
                appointment = db.session.query(Appointment).filter_by(
                    doctor_id=doctor_id, date=date_obj, time=datetime.strptime('08:00:00', '%H:%M:%S').time()
                ).first()
                if morning_not_available and not appointment:
                    patient=db.session.query(Patient).filter_by(username='patient-dummy_001').first()
                    new_appointment=Appointment(
                        doctor_id=doctor_id,
                        patient_id=patient.id,
                        date=date_obj,
                        time=datetime.strptime('08:00:00',"%H:%M:%S").time(),
                        status="Booked"
                    )
                    db.session.add(new_appointment)
            if slot=='afternoon':
                afternoon_not_available='true' in slots
                appointment = db.session.query(Appointment).filter_by(
                    doctor_id=doctor_id, date=date_obj, time=datetime.strptime('16:00:00', '%H:%M:%S').time()
                ).first()
                if afternoon_not_available and not appointment:
                    patient=db.session.query(Patient).filter_by(username='patient-dummy_001').first()
                    new_appointment=Appointment(
                        doctor_id=doctor_id,
                        patient_id=patient.id,
                        date=date_obj,
                        time=datetime.strptime('16:00:00',"%H:%M:%S").time(),
                        status="Booked"
                    )
                    db.session.add(new_appointment)
        db.session.commit()
        return redirect('/doctor/update/availability/'+doctor_id)