from marshmallow import ValidationError
from sqlalchemy.orm import sessionmaker
from flask import jsonify, request, Blueprint
import bcrypt

from database.tables import *
from schemas import *

session = sessionmaker(bind=engine)
s = session()

query = Blueprint("query", __name__)


@query.route('/user/<string:username>', methods=['GET'])
def get_user(username):
    user = s.query(User).filter(User.username == username).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    schema = UserSchema()
    return schema.dump(user), 200


@query.route('/user/<string:username>', methods=['PUT'])
def update_user(username):
    user = s.query(User).filter(User.username == username).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    params = request.json
    if not params:
        return {"message": "No input data provided"}, 400
    schema = UserSchema()
    try:
        data = schema.load(params)
    except ValidationError as err:
        return err.messages, 422
    check_email = s.query(User).filter(User.email == request.json.get('email')).first()
    check_username = s.query(User).filter(User.username == request.json.get('username')).first()
    if check_email is not None and request.json.get('email') != user.email:
        return {"message": "User with provided email already exists"}, 406
    if check_username is not None and request.json.get('username') != username:
        return {"message": "User with provided username already exists"}, 406
    for key, value in params.items():
        setattr(user, key, value)
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    user.password = hashed
    s.commit()
    return schema.dump(data), 200


@query.route('/user/<string:username>', methods=['DELETE'])
def delete_user(username):
    user = s.query(User).filter(User.username == username).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    s.query(CourseMember).filter(CourseMember.userId == user.id).delete(synchronize_session="fetch")
    s.query(Request).filter(Request.requestToLector == user.id).delete(synchronize_session="fetch")
    s.query(Request).filter(Request.studentId == user.id).delete(synchronize_session="fetch")
    s.delete(user)
    s.commit()
    schema = UserSchema()
    return schema.dump(user), 200


# only for lectors
@query.route('/user/acceptrequest/<int:request_id>', methods=['PUT'])
def accept_request(request_id):
    req = s.query(Request).filter(Request.id == request_id).first()
    if req is None:
        return {"message": "Request could not be found."}, 404
    if s.query(CourseMember).filter(CourseMember.courseId == getattr(req, 'requestToCourse')).count() < 5:
        setattr(req, 'status', 'Accepted')
        s.query(Request).filter(Request.id == request_id).delete(synchronize_session="fetch")
        new_course_member = CourseMember(courseId=getattr(req, 'requestToCourse'), userId=getattr(req, 'studentId'))
        s.add(new_course_member)
        s.commit()
    else:
        return {"message": "Request can't be accepted because the limit of students will be exceeded."}, 406
    return {"message": "Accepted"}, 200


# only for lectors
@query.route('/user/declinerequest/<int:request_id>', methods=['PUT'])
def decline_request(request_id):
    req = s.query(Request).filter(Request.id == request_id).first()
    if req is None:
        return {"message": "Request could not be found."}, 404
    setattr(req, 'status', 'Declined')
    s.commit()
    return {"message": "Declined"}, 200


@query.route('/course', methods=['POST'])
def add_course():
    new_course = request.json
    if not new_course:
        return {"message": "No input data provided"}, 400
    schema = CourseSchema()
    try:
        data = schema.load(new_course)
    except ValidationError as err:
        return err.messages, 422
    user_lector = s.query(User).filter(User.id == request.json.get('courseLector')).first()
    if user_lector is None:
        return {"message": "User could not be found."}, 404
    if user_lector.userType != 'Lector':
        return {"message": "This user is not lector."}, 406
    s.add(data)
    s.commit()
    return schema.dump(data), 200


@query.route('/course/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = s.query(Course).filter(Course.id == course_id).first()
    if course is None:
        return {"message": "Course could not be found."}, 404
    schema = CourseSchema()
    return schema.dump(course), 200


# get courses for user with provided id
@query.route('/user/course/<int:user_id>', methods=['GET'])
def get_course_by_userid(user_id):
    courses = s.query(Course).join(CourseMember).filter(CourseMember.userId == user_id).all()
    if not courses:
        return {"message": "Courses could not be found."}, 404
    schema = CourseSchema()
    return jsonify(schema.dump(courses, many=True)), 200


@query.route('/course/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    course = s.query(Course).filter(Course.id == course_id).first()
    if course is None:
        return {"message": "Course could not be found."}, 404
    params = request.json
    if not params:
        return {"message": "No input data provided"}, 400
    schema = CourseSchema()
    try:
        data = schema.load(params)
    except ValidationError as err:
        return err.messages, 422
    user = s.query(User).filter(User.id == request.json.get('courseLector')).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    if user.userType != 'Lector':
        return {"message": "This user is not lector."}, 406
    for key, value in params.items():
        setattr(course, key, value)
    s.commit()
    return schema.dump(data), 200


@query.route('/course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    course = s.query(Course).filter(Course.id == course_id).first()
    if course is None:
        return {"message": "Course could not be found."}, 404
    s.query(CourseMember).filter(CourseMember.courseId == course.id).delete(synchronize_session="fetch")
    s.query(Request).filter(Request.requestToCourse == course.id).delete(synchronize_session="fetch")
    s.delete(course)
    s.commit()
    schema = CourseSchema()
    return schema.dump(course), 200


# only for students
@query.route('/request', methods=['POST'])
def add_request():
    new_request = request.json
    if not new_request:
        return {"message": "No input data provided"}, 400
    schema = RequestSchema()
    try:
        data = schema.load(new_request)
    except ValidationError as err:
        return err.messages, 422
    user_lector = s.query(User).filter(User.id == request.json.get('requestToLector')).first()
    if user_lector is None:
        return {"message": "Lector could not be found."}, 404
    if user_lector.userType != 'Lector':
        return {"message": "This user is not a lector."}, 406
    user_student = s.query(User).filter(User.id == request.json.get('studentId')).first()
    if user_student is None:
        return {"message": "Student could not be found."}, 404
    if user_student.userType != 'Student':
        return {"message": "This user is not a student."}, 406
    course = s.query(Course).filter(Course.id == request.json.get('requestToCourse')).first()
    if course is None:
        return {"message": "Course could not be found."}, 404
    if course.courseLector != user_lector.id:
        return {"message": "Provided lector is not allowed to accept this request."}, 406
    s.add(data)
    s.commit()
    return schema.dump(data), 200


@query.route('/auth/register', methods=['POST'])
def add_user():
    new_user = request.json
    if not new_user:
        return {"message": "No input data provided"}, 400
    schema = UserSchema()
    try:
        schema.load(new_user)
    except ValidationError as err:
        return err.messages, 422
    user_check_email = s.query(User).filter(User.email == request.json.get('email')).first()
    user_check_username = s.query(User).filter(User.username == request.json.get('username')).first()
    if user_check_email is not None:
        return {"message": "User with provided email already exists"}, 406
    if user_check_username is not None:
        return {"message": "User with provided username already exists"}, 406
    user_to_create = User(**new_user)
    hashed = bcrypt.hashpw(user_to_create.password.encode('utf-8'), bcrypt.gensalt())
    user_to_create.password = hashed
    s.add(user_to_create)
    s.commit()
    return schema.dump(user_to_create), 200
