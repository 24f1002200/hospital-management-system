from flask import Flask
from database import db

app=Flask(__name__)

db_name="db.sqlite3"

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+db_name

db.init_app(app)

def create_db():
    with app.app_context():
        db.create_all()

if __name__=="__main__":
    create_db()