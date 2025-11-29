from flask import current_app as app
from flask import render_template, redirect, request, session, abort
from .database import db
from .models import *

@app.route('/view/patient/<username>',methods=["GET"])
@app.route('/view/patient/<username>/<doctor_id>',methods=["GET"])
def patient_history(username,doctor_id=None):
    if session.get('user_type') != 'admin' and session.get('user_type') != 'doctor' and session.get('user_type') != 'patient':
        print(session.get('user_type'))
        return abort(403)
    patient=db.session.query(Patient).filter_by(username=username).first()
    if not patient:
        return abort(404)
    if patient.blacklisted=='true':
        return render_template('blacklisted.html',role='patient',person=patient)
    history=[]
    for i in range(len(patient.appointments)):
        treatments=patient.appointments[i].treatments
        # treatment.notes look like ::::  "<visit_type> ; <tests-done> ; <Medicines>"
        for treatment in treatments:
            app_hist={
                "visit_no":str(i),
                "visit_type":treatment.notes.split(';')[0].strip(),
                "tests_done":treatment.notes.split(';')[1].strip().split(','),
                "diagnosis":treatment.diagnosis,
                "prescription":treatment.prescription,
                "medicines":treatment.notes.split(';')[2].strip().split(',')
            }
            history.append(app_hist)
    if session.get('user_type')=='doctor':
        if not doctor_id:
            return redirect(404)
        doctor=db.session.query(Doctor).filter_by(id=doctor_id).first()
        if not doctor:
            return redirect(404)
    else:
        doctor=None
    return render_template('patient_history.html',patient=patient,history=history,role=session.get('user_type'),doctor=doctor)
