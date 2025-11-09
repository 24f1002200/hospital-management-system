from flask import Flask
from application.database import db
from application.models import *

app=None

def setup():
    app=Flask(__name__)
    db_name="db.sqlite3"
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+db_name
    app.secret_key='secret_@#123'
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.app_context().push()
    admin=Admin(username="admin",password="123456") # Change admin details after..
    admins=db.session.query(Admin).all()
    for admin in admins:
        db.session.delete(admin)
    db.session.add(admin)
    db.session.commit()
    return app

app=setup()
from application.controllers import *

if __name__=="__main__":
    app.run()