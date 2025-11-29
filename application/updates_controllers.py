from flask import current_app as app
from flask import render_template, redirect, request, session, abort
from .database import db
from .models import *

@app.route('/update/patient/history/<appointment_id>',methods=["GET","POST"])
def update_patient_history(appointment_id):
    if session.get('user_type')!='doctor':
        return abort(403)
    appointment=db.session.query(Appointment).filter_by(id=appointment_id).first()
    if not appointment:
        return abort(404)
    if request.method=="GET":
        return render_template('update_patient_history.html',appointment=appointment)
    elif request.method=="POST":
        visit_type=request.form.get('visit_type')
        test_done=request.form.get('test_done') # Comma separated string
        diagnosis=request.form.get('diagnosis')
        medicines=request.form.get('medicines') # Comma separated string
        prescription=request.form.get('prescription')
        # treatment.notes look like ::::  "<visit_type> ; <tests-done> ; <Medicines>"
        notes=f"{visit_type if visit_type else ''} ; {test_done if test_done else ''} ; {medicines if medicines else ''}"
        if appointment.treatments:
            appointment.treatments[0].diagnosis=diagnosis
            appointment.treatments[0].prescription=prescription
            appointment.treatments[0].notes=notes
        else:
            treatment=Treatment(
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes,
                appointment_id=appointment_id
            )
            db.session.add(treatment)
        db.session.commit()
        return redirect('/doctor/'+appointment.doctor.username)

@app.route('/appointment/<action>/<appointment_id>',methods=["GET"])
def update_appointment_status(action,appointment_id):
    if session.get('user_type')!='doctor':
        return abort(403)
    appointment=db.session.query(Appointment).filter_by(id=appointment_id).first()
    if not appointment:
        return abort(404)
    if request.method=="GET":
        if action=='complete':
            appointment.status='Completed'
        elif action=='cancel':
            appointment.status='Cancelled'
        db.session.commit()
        return redirect('/doctor/'+appointment.doctor.username)
