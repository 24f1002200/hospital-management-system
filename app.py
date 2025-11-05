from flask import Flask
from application.database import db
from application.models import *

app=Flask(__name__)

db_name="db.sqlite3"
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+db_name

db.init_app(app)

def create_db():
    with app.app_context():
        db.create_all()
    app.app_context().push()
    admin=Admin(username="admin",password="123456") # Change admin details after..
    admins=db.session.query(Admin).all()
    for admin in admins:
        db.session.delete(admin)
    db.session.add(admin)
    db.session.commit()

from application.controllers import *

if __name__=="__main__":
    create_db()
    # app.run()