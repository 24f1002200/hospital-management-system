from flask import current_app as app
from flask import render_template, redirect, request, session, abort
from .database import db
from .models import *

@app.route('/admin',methods=["GET"])
def admin():
    if session.get('user_type')!='admin':
        return abort(403)
    if request.method=="GET":
        doctor_list=db.session.query(Doctor).all()
        patient_list=db.session.query(Patient).all()
        patient_list=[patient for patient in patient_list if patient.username!='patient-dummy_001']
        appointment_list=db.session.query(Appointment).all()
        appointment_list=[appointment for appointment in appointment_list if appointment.patient.username!='patient-dummy_001']
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
        patient_search_results=[
            patient for patient in patient_search_results
            if patient.username!='patient-dummy_001'
        ]
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
        details=request.form.get('details')

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
        
        doctor=Doctor(username=username, password=password, blacklisted='false',profile_details=details if details else '')
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
