from flask import Flask
from flask import render_template, redirect, request, session, abort
from flask import current_app as app

from .database import db

from .models import *

@app.route('/', methods=["GET","POST"])
def login():
    if request.method=="GET":
        return render_template("login.html")
    else:
        uname=request.form.get("username")
        pwd=request.form.get("password")
        admin=db.session.query(Admin).filter_by(username=uname).first()
        if not admin:
            doctor=db.session.query(Doctor).filter_by(username=uname).first()
            if not doctor:
                patient=db.session.query(Patient).filter_by(username="patient-"+uname).first()
                if not patient:
                    return render_template("user_not_found.html")
                else:
                    if pwd==patient.password:
                        session['user_type']='patient'
                        return redirect('/patient/patient-'+uname)
                    else:
                        return render_template("incorrect_password.html")
            else:
                if pwd==doctor.password:
                    session['user_type']='doctor'
                    return redirect('/doctor/'+uname)
                else:
                    return render_template("incorrect_password.html")
        else:
            if pwd==admin.password:
                session['user_type']='admin'
                return redirect('/admin')
            else:
                return render_template("incorrect_password.html")

@app.route('/register',methods=["GET","POST"])
def register():
    if request.method=="GET":
        return render_template("register.html")
    elif request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        patient=db.session.query(Patient).filter_by(username=username).first()
        if patient:
            return render_template("username_exists.html")
        else:
            patient=Patient(username="patient-"+username, password=password, blacklisted='false')
            db.session.add(patient)
            db.session.commit()
            return render_template("patient_dashboard.html")

@app.route('/admin',methods=["GET"])
def admin():
    if session.get('user_type')!='admin':
        return abort(403)
    if request.method=="GET":
        doctor_list=db.session.query(Doctor).all()
        patient_list=db.session.query(Patient).all()
        appointment_list=db.session.query(Appointment).all()
        return render_template("admin_dashboard.html",doctor_list=doctor_list,patient_list=patient_list,appointment_list=appointment_list)
    
@app.route('/admin/search',methods=["POST"])
def admin_search():
    if session.get('user_type')!='admin':
        return abort(403)
    if request.method=="POST":
        search_string=request.form.get('search-string')
        if not search_string:
            return redirect('/admin')
        search_string="%{}%".format(search_string)
        doctor_search_results=db.session.query(Doctor).filter(Doctor.username.like(search_string)).all()
        patient_search_results=db.session.query(Patient).filter(Patient.username.like(search_string)).all()
        department_search_results=db.session.query(Department).filter(Department.department_name.like(search_string)).all()
        all_doctors=db.session.query(Doctor).all()
        for doctor in all_doctors:
            for department in department_search_results:
                departments=[d.department_name for d in doctor.departments]
                print(departments)
                if department.department_name in departments and doctor not in doctor_search_results:
                    doctor_search_results.append(doctor)
        appointment_list=db.session.query(Appointment).all()
        return render_template("admin_dashboard.html",doctor_list=doctor_search_results,patient_list=patient_search_results,appointment_list=appointment_list)
    
@app.route('/doctor/<username>',methods=["GET","POST"])
def doctor(username):
    if session.get('user_type')!='doctor':
        return abort(403)
    if request.method=="GET":
        doc=db.session.query(Doctor).filter_by(username=username).first()
        if not doc:
            return abort(404)
        return render_template("doctor_dashboard.html",doc=doc)
    
@app.route('/patient/<username>',methods=["GET","POST"])
def patient(username):
    if session.get('user_type')!='patient':
        return abort(403)
    if request.method=="GET":
        pat=db.session.query(Patient).filter_by(username=username).first()
        if not pat:
            return abort(404)
        return render_template("patient_dashboard.html",pat=pat)

@app.route('/register/doctor',methods=["GET","POST"])
def register_doctor():
    if session.get('user_type')!='admin':
        return abort(403)
    if request.method=="GET":
        return render_template("register_doctor.html")
    elif request.method=="POST":
        username=request.form.get("username")
        password=request.form.get("password")
        department=request.form.get("department")

        # Check if doctor exists
        doctor=db.session.query(Doctor).filter_by(username=username).first()
        if doctor:
            return render_template("doctor_exists.html")

        # Create department if it does not exist
        dep=db.session.query(Department).filter_by(department_name=department).first()
        if not dep:
            dep=Department(department_name=department.lower(), description="This is department : "+department)
            db.session.add(dep)
            db.session.commit()
        
        doctor=Doctor(username=username, password=password, blacklisted='false')
        doctor.departments.append(dep)
        db.session.add(doctor)
        db.session.commit()
        return redirect('/admin')

@app.route('/update/<role>/<username>',methods=["GET","POST"])
def update(role,username):
    if session.get('user_type')!='admin':
        return abort(403)
    if role=='doctor':
        doctor=db.session.query(Doctor).filter_by(username=username).first()
        if not doctor:
            return abort(400)
        if request.method=="GET":
            return render_template("update_doctor.html",uname=username)
        elif request.method=="POST":
            new_pass=request.form.get("password")
            new_dept=request.form.get("department")
            append=request.form.get("append")

            if new_pass:
                doctor.password=new_pass
            if new_dept:
                dep=db.session.query(Department).filter_by(department_name=new_dept).first()
                if not dep:
                    dep=Department(department_name=new_dept.lower(), description="This is department : "+new_dept)
                    db.session.add(dep)
                    db.session.commit()
                if dep not in doctor.departments:
                    if not append:
                        doctor.departments.clear()
                    doctor.departments.append(dep)
            db.session.commit()
    elif role=='patient':
        patient=db.session.query(Patient).filter_by(username=username).first()
        if not patient:
            return abort(400)
        if request.method=="GET":
            return render_template("update_patient.html",uname=username)
        elif request.method=="POST":
            new_pass=request.form.get("password")
            if new_pass:
                patient.password=new_pass
            db.session.commit()
    else:
        return abort(404)    
    return redirect('/admin')

@app.route('/delete/<role>/<username>',methods=["GET"])
def delete(role,username):
    if session.get('user_type')!='admin':
        return abort(403)
    if request.method=="GET":
        if role=='doctor':
            doctor=db.session.query(Doctor).filter_by(username=username).first()
            if not doctor:
                return abort(400)
            for appointment in doctor.appointments:
                db.session.delete(appointment)
            doctor.departments.clear()
            db.session.delete(doctor)
            db.session.commit()
        elif role=='patient':
            patient=db.session.query(Patient).filter_by(username=username).first()
            if not patient:
                return abort(400)
            for appointment in patient.appointments:
                db.session.delete(appointment)
            db.session.delete(patient)
            db.session.commit()
        else:
            return abort(404)
        return redirect('/admin')

@app.route('/blacklist/<role>/<username>',methods=["GET"])
def toggle_blacklist(role,username):
    if session.get('user_type')!='admin':
        return abort(403)
    if request.method=="GET":
        if role=='doctor':
            doctor=db.session.query(Doctor).filter_by(username=username).first()
            if not doctor:
                return abort(400)
            if doctor.blacklisted=='true':
                doctor.blacklisted='false'
            elif doctor.blacklisted=='false':
                doctor.blacklisted='true'
            db.session.commit()
        elif role=='patient':
            patient=db.session.query(Patient).filter_by(username=username).first()
            if not patient:
                return abort(400)
            if patient.blacklisted=='true':
                patient.blacklisted='false'
            elif patient.blacklisted=='false':
                patient.blacklisted='true'
            db.session.commit()
        else:
            return abort(404)
        return redirect('/admin')

@app.route('/view/patient/<username>',methods=["GET"])
def patient_history(username):
    if session.get('user_type') != 'admin' and session.get('user_type') != 'doctor' and session.get('user_type') != 'patient':
        print(session.get('user_type'))
        return abort(403)
    patient=db.session.query(Patient).filter_by(username=username).first()
    if not patient:
        return abort(404)
    history=[]
    for i in range(len(patient.appointments)):
        treatment=patient.appointments[i].treatment
        # treatment.notes look like ::::  "<visit_type> ; <tests-done> ; <Medicines>"
        app_hist={
            "visit_no":str(i),
            "visit_type":treatment.notes.split(';')[0].strip(),
            "tests_done":treatment.notes.split(';')[1].strip().split(','),
            "diagnosis":treatment.diagnosis,
            "prescription":treatment.prescription,
            "medicines":treatment.notes.split(';')[2].strip().split(',')
        }
        history.append(app_hist)
    return render_template('patient_history.html',patient=patient,history=history,who=session.get('user_type'))

@app.route('/logout',methods=["GET"])
def logout():
    session.clear()
    return redirect('/')