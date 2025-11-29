from flask import current_app as app
from flask import render_template, redirect, request, session, abort
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
                        if patient.blacklisted=='true':
                            return render_template('blacklisted.html',role='patient',person=patient)
                        else:
                            session['user_type']='patient'
                            return redirect('/patient/patient-'+uname)
                    else:
                        return render_template("incorrect_password.html")
            else:
                if pwd==doctor.password:
                    if doctor.blacklisted=='true':
                        return render_template('blacklisted.html',role='doctor',person=doctor)
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
        patient=db.session.query(Patient).filter_by(username="patient-"+username).first()
        if patient:
            return render_template("username_exists.html")
        else:
            patient=Patient(username="patient-"+username, password=password, blacklisted='false')
            db.session.add(patient)
            db.session.commit()
            session['user_type']='patient'
            return redirect('/patient/'+patient.username)

@app.route('/logout',methods=["GET"])
def logout():
    session.clear()
    return redirect('/')