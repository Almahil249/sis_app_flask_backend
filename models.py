from app import db 
import uuid
class Student(db.Model):
    __tabelname__ ='student'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name= db.Column(db.String, nullable=False)
    gender = db.Column(db.Integer)  
    email = db.Column(db.String, nullable=False, unique=True)
    student_id = db.Column(db.Integer, nullable=False, unique=True)
    password = db.Column(db.String,nullable=False)
    level = db.Column (db.String, nullable=True)
    profile_pic = db.Column(db.LargeBinary, nullable=True)
    token = db.Column(db.String,nullable =False)
    
    def __repr__(self):
        return f'<naem:{self.name}>, <level:{self.level}>'

    def generateToken(self):
        self.token = str(uuid.uuid4())    

    def toMap(self):
        return {
            "name":self.name,
            "email":self.email,
            "password":self.password,
            "gender":self.gender,
            "level":self.level,
            "student_id":self.student_id,
            "profile_pic_path":self.profile_pic
        }

class Store(db.Model):
    __tablename__ = 'store'
    store_id = db.Column(db.Integer, primary_key=True, unique=True)
    store_name = db.Column(db.String, nullable=False)
    store_image = db.Column(db.LargeBinary, nullable=True)
    store_review = db.Column(db.Float, nullable=False, default=0.0)
    store_location_longitude = db.Column(db.Float, nullable=False)
    store_location_latitude = db.Column(db.Float, nullable=False)

    def toMap(self):
        return {
            "store_id": self.store_id,
            "store_name": self.store_name,
            "store_image": self.store_image,
            "store_review": self.store_review,
            "store_location_longitude": self.store_location_longitude,
            "store_location_latitude": self.store_location_latitude
        }
    

class StudentStoresRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    studentid=db.Column(db.Integer)
    storeid = db.Column(db.Integer)

    