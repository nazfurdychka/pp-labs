from marshmallow import Schema, fields, validate, post_load

from database.tables import Course, Request, CourseMember, User


class UserSchema(Schema):
    id = fields.Integer()
    username = fields.Str(validate=validate.Length(max=45), required=True)
    firstName = fields.Str(validate=validate.Length(max=45), required=True)
    lastName = fields.Str(validate=validate.Length(max=45), required=True)
    email = fields.Email(validate=validate.Length(max=100), required=True)
    password = fields.Str(validate=validate.Length(max=100), required=True, load_only=True)
    phone = fields.Str(validate=validate.Length(max=45), required=False)
    userType = fields.Str(validate=validate.OneOf(["Student", "Lector"]), required=True)

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)


class CourseSchema(Schema):
    id = fields.Integer()
    courseName = fields.Str(validate=validate.Length(max=45), required=True)
    courseDescription = fields.Str(validate=validate.Length(max=500), required=True)
    courseLector = fields.Integer(required=True)

    @post_load
    def make_course(self, data, **kwargs):
        return Course(**data)


class RequestSchema(Schema):
    id = fields.Integer()
    studentId = fields.Integer(required=True)
    requestToCourse = fields.Integer(required=True)
    requestToLector = fields.Integer(required=True)
    status = fields.Str(validate=validate.OneOf(["OnHold", "Accepted", "Declined"]), required=False, dump_only= True)

    @post_load
    def make_request(self, data, **kwargs):
        return Request(**data)


class CourseMemberSchema(Schema):
    id = fields.Integer()
    courseId = fields.Integer(required=True)
    userId = fields.Integer(required=True)

    @post_load
    def make_course_member(self, data, **kwargs):
        return CourseMember(**data)
