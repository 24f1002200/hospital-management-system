from flask import Flask
from flask import render_template, redirect, request
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
                        return render_template("patient_dashboard.html")
                    else:
                        return render_template("incorrect_password.html")
            else:
                if pwd==doctor.password:
                    return render_template("doctor_dashboard.html")
                else:
                    return render_template("incorrect_password.html")
        else:
            if pwd==admin.password:
                return render_template("admin_dashboard.html")
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
            patient=Patient(username="patient-"+username, password=password)
            db.session.add(patient)
            db.session.commit()
            return render_template("patient_dashboard.html")