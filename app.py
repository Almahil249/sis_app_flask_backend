from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_OT5QXk8HPyeW@ep-nameless-voice-abu0w3xl.eu-west-2.aws.neon.tech/neondb?sslmode=require'

    app.secret_key = 'SOME KEY'
    

    
    db.init_app(app)

    from routes import register_routes
    register_routes(app, db)

    #import later on

    migrage = Migrate(app,db)
    return app
