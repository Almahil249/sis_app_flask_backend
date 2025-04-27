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
    store_description = db.Column(db.String, nullable=True)

    def toMap(self):
        return {
            "store_id": self.store_id,
            "store_name": self.store_name,
            "store_image": self.store_image,
            "store_review": self.store_review,
            "store_location_longitude": self.store_location_longitude,
            "store_location_latitude": self.store_location_latitude,
            "store_description": self.store_description
        }
    

# remove this class later
class StudentStoresRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    studentid=db.Column(db.Integer)
    storeid = db.Column(db.Integer)

class Item(db.Model):
    __tablename__ = 'item'
    product_id = db.Column(db.Integer, primary_key=True, unique=True)
    product_name = db.Column(db.String, nullable=False)
    product_image = db.Column(db.LargeBinary, nullable=True)
    product_price = db.Column(db.Float, nullable=False)
    product_description = db.Column(db.String, nullable=True)

    def toMap(self):
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_image": self.product_image,
            "product_price": self.product_price,
            "product_description": self.product_description
        }

class StoreItemRelation(db.Model):
    __tablename__ = 'store_item_relation'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.store_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('item.product_id'), nullable=False)

    def toMap(self):
        return {
            "store_id": self.store_id,
            "product_id": self.product_id
        }