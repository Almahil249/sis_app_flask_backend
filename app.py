from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = process.env.DB_URL

    app.secret_key = 'SOME KEY'
    

    
    db.init_app(app)

    from routes import register_routes
    register_routes(app, db)

    #import later on

    migrage = Migrate(app,db)
    return app
