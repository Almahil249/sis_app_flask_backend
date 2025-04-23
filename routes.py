from flask import request,jsonify, render_template, redirect, url_for, session, flash
from models import Student, Store, StudentStoresRelation
from werkzeug.utils import secure_filename
import json
from flask import send_file
import io
import socket  # Import the socket module
socket.setdefaulttimeout(100)  # Set timeout to 120 second
from PIL import Image

def compress_image(image_data, target_size_kb=30, initial_quality=90, step=5):
    """
    Compress image data to a target size in KB.
    image_data: Bytes of the original image
    target_size_kb: Target size in KB (default 30)
    initial_quality: Starting JPEG quality (default 90)
    step: Quality reduction step (default 5)
    Returns: Compressed image bytes
    """
    # Convert bytes to PIL Image
    img = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if image has alpha channel
    if img.mode in ('RGBA', 'LA'):
        img = img.convert('RGB')
    
    quality = initial_quality
    while quality > 0:
        # Create buffer for compressed image
        buffer = io.BytesIO()
        
        # Save image to buffer with current quality
        img.save(buffer, format='JPEG', quality=quality)
        compressed_data = buffer.getvalue()
        
        # Check if size is within target
        size_kb = len(compressed_data) / 1024
        if size_kb <= target_size_kb:
            return compressed_data
            
        # Reduce quality for next iteration
        quality -= step
    
    # If we can't meet target size, return smallest possible
    return compressed_data

def register_routes(app, db):
    @app.route('/')
    def index():
        #print hello world
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
    @app.route("/https://prod.liveshare.vsengsaas.visualstudio.com/join?FBD6455701135B6CB19B0349D7CEB79C4FB1", methods=['GET'])
    def get_default_image():
        # Read the default image file
        with open('DEFAULT_PROFILE_IMAGE.jpg', 'rb') as f:
            default_profile_image = f.read()

        # Compress the image data to reduce size to less than 30 KB
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

        # Determine the image format (default to PNG if unknown)
        image_format = 'png'  # Default format
        if student.profile_pic[:3] == b'\xff\xd8\xff':  # JPEG magic number
            image_format = 'jpeg'

        compressed_image = compress_image(student.profile_pic, target_size_kb=30)
        



        return send_file(
            io.BytesIO(compressed_image),
            mimetype=f'image/{image_format}',
            as_attachment=False,
            download_name=f'student_{student_id}.{image_format}'
        )



    @app.route("/getstudentdata/", methods=['GET'])
    def getStudentData():
        token = request.headers['Authorization']
        student = Student.query.filter(Student.token == token).first()
        if not student:
            return jsonify({'error': 'You Are Not Authorized'}), 400

        student_data = student.toMap()
        # Add profile picture path
        student_data['profile_pic_path'] = f"getstudentdata\\{student.id}\\image" if student.profile_pic else None
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
                # compress the image data to reduce size to less than 30 kb
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
    """
    @app.route("/updatestudentdata/",methods=["PUT"])
    def updateStudentData():
        token = request.headers['Authorization']
        print("token", token)
        data = json.loads(request.form['data'])
        
        student = Student.query.filter(Student.token == token).first()
        email = data['email']
        name = data ['name']
        student_id = data ['student_id']
        password = data['password']
        
        is_exist_student = Student.query.filter(Student.email == email).first()
        if is_exist_student:
            if is_exist_student.token != token:
                return jsonify({"error":"This Email Is Used"}), 400
        
        level,gender = False, False
        try:
            if 'level' in data:
                level = True
            if 'gender' in data:
                gender =True

    
            if 'profile_pic_path' in request.files:
                
                if student.profile_pic and student.profile_pic != 'DEFAULT_PROFILE_IMAGE.png':
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'],"profile_pics",student.profile_pic))

                    profile_pic = request.files['profile_pic_path']
                    profile_pic_extension = str(profile_pic.filename).split(".")[-1]
                    profile_pic_name = secure_filename(str(uuid.uuid4()))+"."+profile_pic_extension
                    profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'],"profile_pics",profile_pic_name)
                    profile_pic.save(profile_pic_path)
                    student.profile_pic = profile_pic_name
                
                elif not student.profile_pic and student.profile_pic != 'DEFAULT_PROFILE_IMAGE.png':
                    profile_pic = request.files['profile_pic_path']
                    profile_pic_extension = str(profile_pic.filename).split(".")[-1]
                    profile_pic_name = secure_filename(str(uuid.uuid4()))+"."+profile_pic_extension
                    profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'],"profile_pics",profile_pic_name)
                    profile_pic.save(profile_pic_path)
                    student.profile_pic = profile_pic_name

            
            elif 'profile_pic_path' in data:
                if student.profile_pic and data['profile_pic_path'] == "DELETE" :
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'],"profile_pics",student.profile_pic))
                    student.profile_pic = None


            student.email= email 
            student.name = name 
            student.student_id= student_id 
            student.password= password 
            if level:
                student.level= data['level']
            if gender:
                student.gender= data['gender']
            db.session.commit()
        except Exception as e:
            return jsonify({'error':str(e)}),400
        return jsonify({"message": "Student Updated Successfully"})
    
    """
    @app.route("/deletestudentaccount/", methods=['DELETE'])
    def deleteStudentAccount():
        token = request.headers['Authorization'].split()[-1]
        student = Student.query.filter(Student.token == token).first()
        if not student:
            return jsonify({'error': "You Are Not Authorized"}), 400

        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student Deleted Successfully"})
############################################################################################################################
            # stores
############################################################################################################################
    @app.route('/stores/<int:store_id>/image', methods=['GET'])
    def get_store_image(store_id):
        store = Store.query.filter_by(store_id=store_id).first()
        if not store or not store.store_image:
            return jsonify({'error': 'Image not found'}), 404

        # Determine the image format (default to PNG if unknown)
        image_format = 'png'  # Default format
        if store.store_image[:3] == b'\xff\xd8\xff':  # JPEG magic number
            image_format = 'jpeg'

        compressed_image = compress_image(store.store_image, target_size_kb=30)

        return send_file(
            io.BytesIO(compressed_image),
            mimetype=f'image/{image_format}',
            as_attachment=False,
            download_name=f'store_{store_id}.{image_format}'
        ) 
    @app.route('/stores/', methods=['GET'])
    def get_stores():
        stores = Store.query.all()
        token = request.headers['Authorization']
        student = Student.query.filter(Student.token == token).first()
        studentid = student.id
        studentFavoStoresData = StudentStoresRelation.query.filter(StudentStoresRelation.studentid== studentid)

        studentFavoStores = []
        for favoStore in studentFavoStoresData:
            studentFavoStores.append(favoStore.storeid)

        for i in range(len(stores)):
            stores[i].store_image = r"/stores/" + str(stores[i].store_id) + r"/image"

        return jsonify({"data":[store.toMap() for store in stores],
                        "favo":studentFavoStores})

    @app.route('/stores/', methods=['POST'])
    def create_store():
        data = json.loads(request.form['data'])
        store = Store(
            store_name=data['store_name'],
            store_review=data['store_review'],
            store_location_longitude=data['store_location_longitude'],
            store_location_latitude=data['store_location_latitude']
        )
        if 'store_img' in request.files:
            store_img = request.files['store_img']
            store.store_image = store_img.read()  # Store the image as binary data
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

        if 'store_img' in request.files:
            store_img = request.files['store_img']
            store.store_image = store_img.read()  # Update the binary image data

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

    @app.route('/stores/addtofavo/',methods=['POST'])
    def addtofavo():
        try:
            data = request.get_json()
            token = request.headers['Authorization']
            
            student = Student.query.filter(Student.token ==token).first()
            studentid = student.id
            storeid = data['storeid']
            print(studentid,storeid)
        except Exception as e:
            print(e)
            return {"message": "You Are Not Authorized","error":str(e)},400
        
        is_exist = StudentStoresRelation.query.filter(StudentStoresRelation.studentid == studentid,StudentStoresRelation.storeid == storeid).first()
        if is_exist:
            return jsonify({"message": "This Relation Is Already Exist"}),400
        studentStoreRelation = StudentStoresRelation(
            studentid =studentid,
            storeid= storeid
        )
        db.session.add(studentStoreRelation)
        db.session.commit()
        return jsonify({"message": "Added successfully to The Favo."}),200

    @app.route('/stores/removefromfavo/',methods=['POST'])
    def removefromfavo():
        try:
            data = request.get_json()
            data = request.get_json()
            token = request.headers['Authorization']
            
            student = Student.query.filter(Student.token ==token).first()
            studentid = student.id
        except Exception as e:
            print(e)
            return {"message": "You Are Not Authorized","error":str(e)},400
        
            
        storeid = data['storeid']
        relation = StudentStoresRelation.query.filter(StudentStoresRelation.studentid == studentid,StudentStoresRelation.storeid == storeid).first()
        if not relation:
            return jsonify({"message": "This Relation Is Not Exist"}),400
        
        db.session.delete(relation)
        db.session.commit()
        return jsonify({"message": "Removed Successfully From The Favo."}),200
        
"""
    @app.route("/getstudentdata/",methods=['GET'])
    def getStudentData():
        token = request.headers['Authorization']
        student = Student.query.filter(Student.token==token).first()
        if not student:
            return jsonify({'error': 'You Are Not Authorized'}), 400
        return jsonify(student.toMap())
    @app.route("/updatestudentdata/", methods=["PUT"])
"""