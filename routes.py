from functools import wraps

from flask_bcrypt import Bcrypt
from flask_httpauth import HTTPBasicAuth
from marshmallow import ValidationError
from sqlalchemy.orm import sessionmaker, Session
from flask import jsonify, request, Blueprint
from database.tables import *
from schema import *

session = sessionmaker(bind=engine)
s: Session = session()

bcrypt = Bcrypt()

query = Blueprint("query", __name__)
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):

    user = s.query(User).filter(User.username == username).one_or_none()
    if user is None:
        return False

    if not bcrypt.check_password_hash(user.password, password):
        return False

    return user


def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if auth.current_user().userType != permission:
                return {"message": "Forbidden"}, 403
            return func(*args, **kwargs)
        return decorated_function
    return decorator


@query.route('/user/<string:username>', methods=['GET'])
@auth.login_required
def get_user(username):
    user = s.query(User).filter(User.username == username).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    if auth.username() != s.query(User).filter_by(username=username).first().username:
        return {"message": "Forbidden"}, 403
    schema = UserSchema()
    return schema.dump(user), 200


@query.route('/user/<string:username>', methods=['PUT'])
@auth.login_required
def update_user(username):
    user = s.query(User).filter(User.username == username).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    if auth.username() != s.query(User).filter_by(username=username).first().username:
        return {"message": "Forbidden"}, 403
    params = request.json
    if not params:
        return {"message": "No input data provided"}, 400
    if 'id' in params:
        return {"message": "You can not change id"}, 400                                                                                            # pragma: no cover
    schema = UserSchema()
    try:
        data = schema.load(params)
    except ValidationError as err:
        return err.messages, 422
    check_username = s.query(User).filter(User.username == request.json.get('username')).first()
    if check_username is not None and request.json.get('username') != username:
        return {"message": "User with provided username already exists"}, 406                                                                       # pragma: no cover
    for key, value in params.items():
        setattr(user, key, value)
    hashed = Bcrypt().generate_password_hash(params['password']).decode('utf - 8')
    user.password = hashed
    s.commit()
    return schema.dump(data), 200


@query.route('/user/<string:username>', methods=['DELETE'])
@auth.login_required()
def delete_user(username):
    user = s.query(User).filter(User.username == username).first()
    if user is None:
        return {"message": "User could not be found."}, 404
    if auth.username() != s.query(User).filter_by(username=username).first().username:
        return {"message": "Forbidden"}, 403
    s.query(CourseMember).filter(CourseMember.userId == user.id).delete(synchronize_session="fetch")
    s.query(Request).filter(Request.requestToLector == user.id).delete(synchronize_session="fetch")
    s.query(Request).filter(Request.studentId == user.id).delete(synchronize_session="fetch")
    s.delete(user)
    s.commit()
    schema = UserSchema()
    return schema.dump(user), 200


@query.route('/user/acceptrequest/<int:request_id>', methods=['PUT'])
@auth.login_required()
@permission_required('Lector')
def accept_request(request_id):
    req = s.query(Request).filter(Request.id == request_id).first()
    if req is None:
        return {"message": "Request could not be found."}, 404
    if s.query(CourseMember).filter(CourseMember.courseId == getattr(req, 'requestToCourse')).count() <= 5:
        setattr(req, 'status', 'Accepted')
        s.query(Request).filter(Request.id == request_id).delete(synchronize_session="fetch")
        new_course_member = CourseMember(courseId=getattr(req, 'requestToCourse'), userId=getattr(req, 'studentId'))
        s.add(new_course_member)
        s.commit()
    else:
        return {"message": "Request can't be accepted because the limit of students will be exceeded."}, 406
    return {"message": "Accepted"}, 200


@query.route('/user/declinerequest/<int:request_id>', methods=['PUT'])
@auth.login_required()
@permission_required('Lector')
def decline_request(request_id):
    req = s.query(Request).filter(Request.id == request_id).first()
    if req is None:
        return {"message": "Request could not be found."}, 404
    setattr(req, 'status', 'Declined')
    s.commit()
    return {"message": "Declined"}, 200


@query.route('/course', methods=['POST'])
@auth.login_required()
@permission_required('Lector')
def add_course():
    new_course_json = request.json
    if not new_course_json:
        return {"message": "No input data provided"}, 400
    if 'id' in new_course_json:
        return {"message": "You can not change id"}, 400                                                                                                         # pragma: no cover
    schema = CourseSchema()
    try:
        data = schema.load(new_course_json)
    except ValidationError as err:
        return err.messages, 422
    user_lector = s.query(User).filter(User.id == request.json.get('courseLector')).first()
    if user_lector is None:
        return {"message": "User could not be found."}, 404                                                                                                      # pragma: no cover
    if user_lector.userType != 'Lector':
        return {"message": "This user is not lector."}, 406
    s.add(data)
    s.commit()
    return schema.dump(data), 200


@query.route('/course/<int:course_id>', methods=['GET'])
@auth.login_required()
def get_course(course_id):
    course = s.query(Course).filter(Course.id == course_id).first()
    if course is None:
        return {"message": "Course could not be found."}, 404                                                                                                    # pragma: no cover
    schema = CourseSchema()
    return schema.dump(course), 200


# get courses for user with provided id
@query.route('/user/course', methods=['GET'])
@auth.login_required()
@permission_required('Lector')
def get_course_by_userid():
    courses = s.query(Course).filter(Course.courseLector == auth.current_user().id).all()
    if not courses:
        return {"message": "Courses could not be found."}, 404
    schema = CourseSchema()
    return jsonify(schema.dump(courses, many=True)), 200


@query.route('/course/<int:course_id>', methods=['PUT'])
@auth.login_required()
@permission_required('Lector')
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
        return {"message": "This user is not lector."}, 406                                                                                                      # pragma: no cover
    for key, value in params.items():
        setattr(course, key, value)
    s.commit()
    return schema.dump(data), 200


@query.route('/course/<int:course_id>', methods=['DELETE'])
@auth.login_required()
@permission_required('Lector')
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


@query.route('/request', methods=['POST'])
@auth.login_required()
@permission_required('Student')
def add_request():
    new_request = request.json
    if not new_request:
        return {"message": "No input data provided"}, 400
    if 'id' in new_request:
        return {"message": "You can not change id"}, 400
    schema = RequestSchema()
    try:
        data = schema.load(new_request)
    except ValidationError as err:
        return err.messages, 422
    user_student = s.query(User).filter(User.id == request.json.get('studentId')).first()
    if user_student is None:
        return {"message": "Student could not be found."}, 404
    if new_request['studentId'] != auth.current_user().id:
        return {"message": "Forbidden"}, 403
    user_lector = s.query(User).filter(User.id == request.json.get('requestToLector')).first()
    if user_lector is None:
        return {"message": "Lector could not be found."}, 404
    if user_lector.userType != 'Lector':
        return {"message": "This user is not a lector."}, 406
    if user_student.userType != 'Student':
        return {"message": "This user is not a student."}, 406
    course = s.query(Course).filter(Course.id == request.json.get('requestToCourse')).first()
    request_to_join = s.query(Request).filter(Request.id == request.json.get('requestToCourse')).all()
    if len(request_to_join) == 1:
        return {"message": "Request was already sent."}, 406
    if course is None:
        return {"message": "Course could not be found."}, 404
    if course.courseLector != user_lector.id:
        return {"message": "Provided lector is not allowed to accept this request."}, 406

    s.add(data)
    s.commit()
    return schema.dump(data), 200


@query.route('/auth/register', methods=['POST'])
def add_user():
    new_user_json = request.json
    if not new_user_json:
        return {"message": "No input data provided"}, 400
    schema = UserSchema()
    try:
        schema.load(new_user_json)
    except ValidationError as err:
        return err.messages, 422
    if s.query(User).filter(User.username == request.json.get('username')).first() is not None:
        return {"message": "User with provided username already exists"}, 406
    user_to_create = User(**new_user_json)
    hashed_password = bcrypt.generate_password_hash(new_user_json['password'])
    user_to_create.password = hashed_password
    s.add(user_to_create)
    s.commit()
    return schema.dump(user_to_create), 200
