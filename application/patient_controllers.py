from flask import current_app as app
from flask import render_template, redirect, request, session, abort
from .database import db
from .models import *

@app.route('/patient/<username>',methods=["GET","POST"])
def patient(username):
    if session.get('user_type')!='patient':
        return abort(403)
    if request.method=="GET":
        pat=db.session.query(Patient).filter_by(username=username).first()
        if not pat:
            return abort(404)
        appointments=db.session.query(Appointment).filter_by(patient_id=pat.id).all()
        from datetime import datetime
        now=datetime.now()
        appointments=[
            appointment for appointment in appointments
            if appointment.status=='Booked' and appointment.date>=now.date() and appointment.doctor.blacklisted=='false'
        ]
        departments=db.session.query(Department).all()
        profile=[]
        if pat.profile_details:
            profile=pat.profile_details.split(' ; ')
        return render_template("patient_dashboard.html",pat=pat,appointments=appointments,departments=departments,profile=profile)
    
@app.route('/update/patient/profile/<username>',methods=['GET','POST'])
def update_profile(username):
    if session['user_type']!='patient':
        return abort(403)
    patient=db.session.query(Patient).filter_by(username=username).first()
    if not patient:
        return 404
    if patient.blacklisted=='true':
        return render_template('blacklisted.html',role='patient',person=patient)
    if request.method=='GET':
        profile=[]
        if patient.profile_details:
            profile=list(map(lambda x:x.strip(),patient.profile_details.split(' ; ')))
        return render_template('update_patient_profile.html',pat=patient,profile=profile)
    elif request.method=='POST':
        name=request.form.get('name')
        contact=request.form.get('contact')
        existing_profile = patient.profile_details.split(' ; ') if patient.profile_details else ["", ""]
        updated_name = name if name else existing_profile[0].strip()
        updated_contact = contact if contact else existing_profile[1].strip()
        patient.profile_details = f"{updated_name} ; {updated_contact}"
        db.session.commit()
        return redirect('/patient/'+patient.username)

@app.route('/view/department/<id>/<pat_id>',methods=['GET'])
def view_department(id,pat_id):
    if session.get('user_type')!='patient':
        return abort(403)
    patient=db.session.query(Patient).filter_by(id=pat_id).first()
    if not patient:
        return abort(404)
    if patient.blacklisted=='true':
        return render_template('blacklisted.html',role='patient',person=patient)
    department=db.session.query(Department).filter_by(id=id).first()
    if not department:
        return abort(404)
    if request.method=='GET':
        return render_template('department_details.html',patient=patient,department=department)

@app.route('/appointment/patient/cancel/<id>',methods=['GET'])
def cancel_patient_appointment(id):
    if session.get('user_type')!='patient':
        return abort(403)
    appointment=db.session.query(Appointment).filter_by(id=id).first()
    if not appointment:
        return abort(404)
    if appointment.patient.blacklisted=='true':
        return abort(403)
    appointment.status='Cancelled'
    db.session.commit()
    return redirect('/patient/'+appointment.patient.username)

@app.route('/appointment/patient/modify/<id>',methods=['GET','POST'])
def modify_patient_appointment(id):
    if session.get('user_type')!='patient':
        return abort(403)
    appointment=db.session.query(Appointment).filter_by(id=id).first()
    if not appointment:
        return abort(404)
    doctor=db.session.query(Doctor).filter_by(id=appointment.doctor.id).first()
    if not doctor:
        return abort(404)
    patient=db.session.query(Patient).filter_by(id=appointment.patient.id).first()
    if not patient:
        return abort(404)
    if request.method=='GET':
        from datetime import datetime
        availability=get_doctor_availability(appointment.doctor.id)
        slot=dict()
        slot['date']=appointment.date.strftime('%d-%m-%Y')
        slot['time']='morning' if appointment.time==datetime.strptime('08:00:00','%H:%M:%S').time() else 'afternoon'
        return render_template('modify_appointment.html',patient=patient,availability=availability,doctor=doctor,appointment=appointment,slot=slot)
    elif request.method=='POST':
        from datetime import datetime
        selected_slot=request.form.get('availability')
        if not selected_slot:
            return redirect('/patient/'+patient.username)
        date_str,time_str=selected_slot.split(';')
        date_obj=datetime.strptime(date_str,'%d-%m-%Y').date()
        time_obj=datetime.strptime('08:00:00' if time_str=='morning' else '16:00:00','%H:%M:%S').time()
        appointment.date=date_obj
        appointment.time=time_obj
        db.session.commit()
        return redirect('/patient/'+patient.username)
    
@app.route('/patient/doctor/availability/<patient_id>/<doctor_id>',methods=['GET','POST'])
def doctor_availability(patient_id,doctor_id):
    if session.get('user_type')!='patient':
        return abort(403)
    patient=db.session.query(Patient).filter_by(id=patient_id).first()
    if not patient:
        return abort(404)
    doctor=db.session.query(Doctor).filter_by(id=doctor_id).first()
    if patient.blacklisted=='true':
        return render_template('blacklisted.html',role='patient',person=patient)
    if not doctor:
        return abort(404)
    if doctor.blacklisted=='true':
        return render_template('blacklisted.html',role='doctor',person=doctor)
    if request.method=='GET':
        availability=get_doctor_availability(doctor_id)
        return render_template('book_doctor.html',doctor=doctor,availability=availability,patient=patient)
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
                    patient=db.session.query(Patient).filter_by(username=patient.username).first()
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
                    patient=db.session.query(Patient).filter_by(username=patient.username).first()
                    new_appointment=Appointment(
                        doctor_id=doctor_id,
                        patient_id=patient.id,
                        date=date_obj,
                        time=datetime.strptime('16:00:00',"%H:%M:%S").time(),
                        status="Booked"
                    )
                    db.session.add(new_appointment)
        db.session.commit()
        return redirect('/patient/'+patient.username)
    
@app.route('/view/doctor/details/<doc_id>/<pat_id>',methods=['GET'])
def view_doctor(doc_id,pat_id):
    if session.get('user_type')!='patient':
        return abort(403)
    patient=db.session.query(Patient).filter_by(id=pat_id).first()
    if not patient:
        return abort(404)
    if patient.blacklisted=='true':
        return render_template('blacklisted.html',role='patient',person=patient)
    doctor=db.session.query(Doctor).filter_by(id=doc_id).first()
    if not doctor:
        return abort(404)
    if doctor.blacklisted=='true':
        return abort(403)
    if request.method=='GET':
        return render_template('doctor_details.html',doctor=doctor,patient=patient)

# not a route
def get_doctor_availability(doctor_id):
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
    return availability