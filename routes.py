from flask import request,jsonify
from models import Student, Store,  Item, StoreItemRelation
import json
from flask import send_file
import io
import socket 
socket.setdefaulttimeout(100)  # Set timeout to 120 second
from PIL import Image

def compress_image(image_data, target_size_kb=30, initial_quality=90, step=5):
    img = Image.open(io.BytesIO(image_data))
    if img.mode in ('RGBA', 'LA'):
        img = img.convert('RGB')

    quality = initial_quality
    while quality > 0:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        compressed_data = buffer.getvalue()

        size_kb = len(compressed_data) / 1024
        if size_kb <= target_size_kb:
            return compressed_data
        quality -= step
    return compressed_data

def register_routes(app, db):
    @app.route('/')
    def index():
        print("Hello World")
        return "Hello World"
    
    @app.route('/login/',methods=['POST'])
    def login():
        data = request.get_json()
        student = Student.query.filter( Student.email == data['email']).first()
        print(data['email'])
        if not student:
            return jsonify({'error': 'There Is No Student With This Email'}), 400
            
        if student.password != data['password'] :
            return jsonify({"error": 'Wrong Password'}), 400
        return jsonify({'message':'Login Successfully','token':student.token})
    
    @app.route('/signup/',methods=['POST'])
    def signup():
        
        data = request.get_json()
        print("data",data)
        email = data['email']
        name = data ['name']
        student_id = data ['student_id']
        password = data['password']
        is_exist = Student.query.filter(Student.email == email).first()
        print(email)
        if is_exist:
            return jsonify({"error": "There Are Already Account With This Email"}),400 
        level,gender = False, False

        if 'level' in data:
            level = True
        if 'gender' in data:
            gender =True

        student = Student(
            email=email,
            name = name,
            student_id= student_id,
            password= password,
        )
                # read DEFAULT_PROFILE_IMAGE.jpg and store it in the database (Large Binary)
        with open('DEFAULT_PROFILE_IMAGE.jpg', 'rb') as f:
            default_profile_image = f.read()
        default_profile_image = compress_image(default_profile_image, target_size_kb=30)
        student.profile_pic = default_profile_image
        print("data['gender']",data['gender'])
        if level:
            student.level= data['level']
        if gender:
            student.gender= data['gender']
        student.generateToken()
        db.session.add(student)
        db.session.commit()
        return jsonify({'message':"User Created Successfully","token":student.token})
    
###########################################################
###########image getter####################################
###########################################################
    @app.route("/DEFAULT_PROFILE_IMAGE", methods=['GET'])
    def get_default_image():
        # Read the default image file
        with open('DEFAULT_PROFILE_IMAGE.jpg', 'rb') as f:
            default_profile_image = f.read()
        compressed_image = compress_image(default_profile_image, target_size_kb=30)
        return send_file(
            io.BytesIO(compressed_image),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='default_profile_image.jpg'
        )
    @app.route("/getstudentdata/<int:student_id>/image", methods=['GET'])
    def get_student_image(student_id):
        student = Student.query.filter_by(id=student_id).first()
        if not student or not student.profile_pic:
            return jsonify({'error': 'Image not found'}), 404
        image_format = 'png'  # Default format
        if student.profile_pic[:3] == b'\xff\xd8\xff':  # JPEG magic number
            image_format = 'jpeg'
        compressed_image = compress_image(student.profile_pic, target_size_kb=30)
        return send_file(
            io.BytesIO(compressed_image),
            mimetype=f'image/{image_format}',
            as_attachment=False,
            download_name=f'student_{student_id}.{image_format}')

    @app.route("/getstudentdata/", methods=['GET'])
    def getStudentData():
        token = request.headers['Authorization']
        student = Student.query.filter(Student.token == token).first()
        if not student:
            return jsonify({'error': 'You Are Not Authorized'}), 400
        student_data = student.toMap()
        student_data['profile_pic_path'] = f"getstudentdata/{student.id}/image" if student.profile_pic else None
        return jsonify(student_data), 200

    @app.route("/updatestudentdata/", methods=['PUT'])
    def updateStudentData():
        token = request.headers['Authorization']
        print("token", token)
        data = json.loads(request.form['data'])
        student = Student.query.filter(Student.token == token).first()
        if not student:
            return jsonify({'error': 'You Are Not Authorized'}), 400
        email = data['email']
        name = data['name']
        student_id = data['student_id']
        password = data['password']
        is_exist_student = Student.query.filter(Student.email == email).first()
        if is_exist_student and is_exist_student.token != token:
            return jsonify({"error": "This Email Is Used"}), 400
        try:
            if 'profile_pic_path' in request.files:
                profile_pic = request.files['profile_pic_path']
                student.profile_pic = profile_pic.read()  # Store binary data
                student.profile_pic = compress_image(student.profile_pic, target_size_kb=30)
            elif 'profile_pic_path' in data and data['profile_pic_path'] == "DELETE":
                with open('DEFAULT_PROFILE_IMAGE.jpg', 'rb') as f:
                    default_profile_image = f.read()
                default_profile_image = compress_image(default_profile_image, target_size_kb=30)
                student.profile_pic = default_profile_image
            student.email = email
            student.name = name
            student.student_id = student_id
            student.password = password
            if 'level' in data:
                student.level = data['level']
            if 'gender' in data:
                student.gender = data['gender']
            db.session.commit()
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        return jsonify({"message": "Student Updated Successfully"})

    @app.route("/deletestudentaccount/", methods=['DELETE'])
    def deleteStudentAccount():
        token = request.headers['Authorization'].split()[-1]
        student = Student.query.filter(Student.token == token).first()
        if not student:
            return jsonify({'error': "You Are Not Authorized"}), 400
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student Deleted Successfully"}), 200
############################################################################################################################
            # stores
############################################################################################################################
    @app.route('/stores/<int:store_id>/image', methods=['GET'])
    def get_store_image(store_id):
        store = Store.query.filter_by(store_id=store_id).first()
        if not store or not store.store_image:
            return jsonify({'error': 'Image not found'}), 404
        image_format = 'png'  # Default format
        if store.store_image[:3] == b'\xff\xd8\xff':  # JPEG magic number
            image_format = 'jpeg'
        compressed_image = compress_image(store.store_image, target_size_kb=30)
        return send_file(
            io.BytesIO(compressed_image),
            mimetype=f'image/{image_format}',
            as_attachment=False,
            download_name=f'store_{store_id}.{image_format}') 
    @app.route('/stores/', methods=['GET'])
    def get_stores():
        stores = Store.query.all()

        for i in range(len(stores)):
            stores[i].store_image = r"/stores/" + str(stores[i].store_id) + r"/image"

        return jsonify({"data":[store.toMap() for store in stores]}) 

    @app.route('/stores/', methods=['POST'])
    def create_store():
        data = json.loads(request.form['data'])
        store = Store(
            store_name=data['store_name'],
            store_review=data['store_review'],
            store_location_longitude=data['store_location_longitude'],
            store_location_latitude=data['store_location_latitude'],
            store_description=data['store_description'] 
            )
        if 'store_img' in request.files:
            store_img = request.files['store_img']
            store.store_image = store_img.read() 
        else:
            return jsonify({"error": "Error In Store Image"}), 400
        db.session.add(store)
        db.session.commit()
        return jsonify({'message': 'Store created successfully'}), 200

    @app.route('/stores/<int:store_id>/', methods=['PUT'])
    def update_store(store_id):
        data = request.form
        store = Store.query.filter_by(store_id=store_id).first()
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        store.store_name = data.get('store_name', store.store_name)
        store.store_review = data.get('store_review', store.store_review)
        store.store_location_longitude = data.get('store_location_longitude', store.store_location_longitude)
        store.store_location_latitude = data.get('store_location_latitude', store.store_location_latitude)
        store.store_description = data.get('store_description', store.store_description)  
        if 'store_img' in request.files:
            store_img = request.files['store_img']
            store.store_image = store_img.read()  
        db.session.commit()
        return jsonify({'message': 'Store updated successfully', 'store': store.toMap()})
    
    @app.route('/stores/<int:store_id>/', methods=['DELETE'])
    def delete_store(store_id):
        store = Store.query.filter_by(store_id=store_id).first()
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        db.session.delete(store)
        db.session.commit()
        return jsonify({'message': 'Store deleted successfully'})

############################################################################################################################
# Items
############################################################################################################################
    # create a image getter for items
    @app.route('/items/<int:product_id>/image', methods=['GET'])
    def get_item_image(product_id):
        item = Item.query.filter_by(product_id=product_id).first()
        if not item or not item.product_image:
            return jsonify({'error': 'Image not found'}), 404
        image_format = 'png' 
        if item.product_image[:3] == b'\xff\xd8\xff':  # JPEG magic number
            image_format = 'jpeg'
        compressed_image = compress_image(item.product_image, target_size_kb=30)
        return send_file(
            io.BytesIO(compressed_image),
            mimetype=f'image/{image_format}',
            as_attachment=False,
            download_name=f'item_{product_id}.{image_format}' )

    @app.route('/items/', methods=['GET'])
    def get_items():
        """
        Retrieve all items from the database.
        """
        items = Item.query.all()
        for i in range(len(items)):
            items[i].product_image = r"/items/" + str(items[i].product_id) + r"/image"
        return jsonify({"data": [item.toMap() for item in items]}), 200

    @app.route('/items/', methods=['POST'])
    def create_item():
        """
        Create a new item in the database.
        """
        data = json.loads(request.form['data'])
        item = Item(
            product_name=data['product_name'],
            product_price=data['product_price'],
            product_description=data.get('product_description', None) )
        if 'product_image' in request.files:
            product_image = request.files['product_image']
            item.product_image = product_image.read()  
        db.session.add(item)
        db.session.commit()
        return jsonify({'message': 'Item created successfully', 'item': item.toMap()}), 200


    @app.route('/items/<int:product_id>/', methods=['PUT'])
    def update_item(product_id):
        """
        Update an existing item in the database.
        """
        data = request.form
        item = Item.query.filter_by(product_id=product_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        item.product_name = data.get('product_name', item.product_name)
        item.product_price = data.get('product_price', item.product_price)
        item.product_description = data.get('product_description', item.product_description)
        if 'product_image' in request.files:
            product_image = request.files['product_image']
            item.product_image = product_image.read()
        db.session.commit()
        return jsonify({'message': 'Item updated successfully', 'item': item.toMap()}), 200

    @app.route('/items/<int:product_id>/', methods=['DELETE'])
    def delete_item(product_id):
        """
        Delete an item from the database.
        """
        item = Item.query.filter_by(product_id=product_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        store_item_relations = StoreItemRelation.query.filter_by(product_id=product_id).all()
        for relation in store_item_relations:
            db.session.delete(relation)

        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Item deleted successfully'}), 200

############################################################################################################################
# Store-Item Relations
############################################################################################################################

    @app.route('/stores_items/', methods=['GET'])
    def get_store_item_relations():
        relations = StoreItemRelation.query.all()
        return jsonify({"data": [relation.toMap() for relation in relations]}), 200
    
    # add item to store /stores_items/store_id/product_id
    @app.route('/stores_items/<int:store_id>/<int:product_id>', methods=['POST'])
    def add_item_to_store(store_id, product_id):
        store = Store.query.filter_by(store_id=store_id).first()
        item = Item.query.filter_by(product_id=product_id).first()
        if not store or not item:
            return jsonify({'error': 'Store or Item not found'}), 404
        relation = StoreItemRelation(
            store_id=store.store_id,
            product_id=item.product_id
        )
        db.session.add(relation)
        db.session.commit()
        return jsonify({'message': 'Item added to store successfully'}), 200
    
    @app.route('/stores_items/<int:store_id>/<int:product_id>', methods=['DELETE'])
    def remove_item_from_store(store_id, product_id):
        relation = StoreItemRelation.query.filter_by(store_id=store_id, product_id=product_id).first()
        if not relation:
            return jsonify({'error': 'Relation not found'}), 404
        db.session.delete(relation)
        db.session.commit()
        return jsonify({'message': 'Item removed from store successfully'}), 200
