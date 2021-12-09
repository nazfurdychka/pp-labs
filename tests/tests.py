import base64
import unittest
import requests

from routes import *
from app import app

url = "http://127.0.0.1:5000/"


class TestUserInteraction(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

        self.student_username = "student1"
        self.student_password = "12345"
        self.lector_username = "lector1"
        self.lector_password = "12345"

        self.test_student = {"username": "student1", "firstName": "firstName", "lastName": "lastName",
                             "email": "student1@gmail.com", "password": "12345", "phone": "123456789",
                             "userType": "Student"}
        self.test_lector = {"username": "lector1", "firstName": "firstName", "lastName": "lastName",
                            "email": "lector1@gmail.com", "password": "12345", "phone": "123456789",
                            "userType": "Lector"}

        self.auth_student_headers = {'Authorization': f'Basic ' + base64.b64encode(b"student1:12345").decode("UTF-8")}
        self.auth_lector_headers = {'Authorization': f'Basic ' + base64.b64encode(b"lector1:12345").decode("UTF-8")}

    def tearDown(self) -> None:
        s.execute("DELETE FROM request")
        s.commit()
        s.execute("DELETE FROM course")
        s.commit()
        s.execute("DELETE FROM user")
        s.commit()

    def testAddUser(self):
        addUserUrl = url + 'auth/register'
        test_student_correct = {
            "username": self.student_username,
            "firstName": "firstName",
            "lastName": "lastName",
            "email": f"{self.student_username}@gmail.com",
            "password": self.student_password,
            "phone": "123456789",
            "userType": "Student"
        }
        test_lector_correct = {
            "username": self.lector_username,
            "firstName": "firstName",
            "lastName": "lastName",
            "email": f"{self.lector_username}@gmail.com",
            "password": self.lector_password,
            "phone": "123456789",
            "userType": "Lector"
        }

        resp1 = self.client.post(addUserUrl, json=test_student_correct)
        resp11 = self.client.post(addUserUrl, json=test_student_correct)
        resp2 = self.client.post(addUserUrl, json=test_lector_correct)
        resp22 = self.client.post(addUserUrl, json=test_lector_correct)
        self.assertEqual(200, resp1.status_code)
        self.assertEqual(200, resp2.status_code)
        self.assertEqual(406, resp11.status_code)
        self.assertEqual(406, resp22.status_code)
        student_in_db = s.query(User.id).filter(User.username == self.student_username).scalar()
        lector_in_db = s.query(User.id).filter(User.username == self.lector_username).scalar()
        self.assertIsNotNone(student_in_db)
        self.assertIsNotNone(lector_in_db)

        self.assertEqual(400, self.client.post(addUserUrl, json={}).status_code)
        self.assertEqual(422, self.client.post(addUserUrl, json={"field": "value"}).status_code)

    def testGetUser(self):
        get_user_url = url + 'user/'
        student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        self.client.post('/auth/register', json=self.test_lector)

        self.assertEqual(200, self.client.get(get_user_url+self.student_username, headers=self.auth_student_headers).status_code)
        self.assertEqual(200, self.client.get(get_user_url+self.lector_username, headers=self.auth_lector_headers).status_code)
        self.assertEqual(404, self.client.get(get_user_url+'sdjfjksdfhkljdshsdjg', headers=self.auth_lector_headers).status_code)
        self.assertEqual(403, self.client.get(get_user_url+self.lector_username, headers=self.auth_student_headers).status_code)

        expected_response = {
            "id": student_id,
            "username": self.student_username,
            "firstName": "firstName",
            "lastName": "lastName",
            "email": f"{self.student_username}@gmail.com",
            "phone": "123456789",
            "userType": "Student"
        }
        self.assertEqual(expected_response, self.client.get(get_user_url+self.student_username, headers=self.auth_student_headers).json)

    def testUpdateUser(self):
        update_user_url = 'user/'
        self.client.post('/auth/register', json=self.test_student)
        self.client.post('/auth/register', json=self.test_lector)

        new_student = {
            "username": self.student_username,
            "firstName": "changedFirstName",
            "lastName": "changedLastName",
            "email": f"{self.student_username}@gmail.com",
            "password": self.student_password,
            "phone": "123456789",
            "userType": "Student"
        }
        self.assertEqual(404, self.client.put(update_user_url+"sjkfhdskjfhds", headers=self.auth_student_headers, json={}).status_code)
        self.assertEqual(403, self.client.put(update_user_url+self.lector_username, headers=self.auth_student_headers, json={}).status_code)
        self.assertEqual(400, self.client.put(update_user_url+self.student_username, headers=self.auth_student_headers, json={}).status_code)
        self.assertEqual(422, self.client.put(update_user_url+self.student_username, headers=self.auth_student_headers, json={"field": "value"}).status_code)
        self.assertEqual(200, self.client.put(update_user_url+self.student_username, headers=self.auth_student_headers, json=new_student).status_code)

    def testDeleteUser(self):
        get_user_url = url + 'user/'
        test_new_user = {
            "username": "newUser",
            "firstName": "firstName",
            "lastName": "lastName",
            "email": "new_user@gmail.com",
            "password": "12345",
            "phone": "123456789",
            "userType": "Student"
        }
        new_user_auth_headers = {'Authorization': 'Basic '+base64.b64encode(b"newUser:12345").decode("UTF-8")}
        self.client.post('/auth/register', json=self.test_student)
        self.client.post('/auth/register', json=self.test_lector)
        self.client.post('auth/register', json=test_new_user)

        self.assertEqual(403, self.client.delete(get_user_url+self.student_username, headers=new_user_auth_headers).status_code)
        self.assertEqual(404, self.client.delete(get_user_url+'sdjfjksdfhkljdshsdjg', headers=new_user_auth_headers).status_code)
        self.assertEqual(200, self.client.delete(get_user_url+'newUser', headers=new_user_auth_headers).status_code)

    def testAddRequest(self):
        addRequestUrl = '/request'
        student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        lector_id = int(self.client.post('/auth/register', json=self.test_lector).json.get('id'))
        course_id = int(self.client.post('/course', headers=self.auth_lector_headers, json={"courseName": "dsjfkdsjk", "courseDescription": "ksfdjfdslkj", "courseLector": lector_id}).json.get('id'))

        test_request = {
            "studentId": student_id,
            "requestToCourse": course_id,
            "requestToLector": lector_id,
        }
        request_with_wrong_student = {
            "studentId": student_id+100,
            "requestToCourse": course_id,
            "requestToLector": lector_id,
        }

        self.assertEqual(400, self.client.post(addRequestUrl, headers=self.auth_student_headers, json={}).status_code)
        self.assertEqual(422, self.client.post(addRequestUrl, headers=self.auth_student_headers, json={"field": "value"}).status_code)
        self.assertEqual(404, self.client.post(addRequestUrl, headers=self.auth_student_headers, json=request_with_wrong_student).status_code)
        self.assertEqual(200, self.client.post(addRequestUrl, headers=self.auth_student_headers, json=test_request).status_code)


class TestCourseInteraction(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

        self.course_name = "course1"

        self.test_student = {"username": "student1", "firstName": "firstName", "lastName": "lastName", "email": "student1@gmail.com", "password": "12345", "phone": "123456789", "userType": "Student"}
        self.test_lector = {"username": "lector1", "firstName": "firstName", "lastName": "lastName", "email": "lector1@gmail.com", "password": "12345", "phone": "123456789", "userType": "Lector"}

        self.auth_student_headers = {'Authorization': f'Basic ' + base64.b64encode(b"student1:12345").decode("UTF-8")}
        self.auth_lector_headers = {'Authorization': f'Basic ' + base64.b64encode(b"lector1:12345").decode("UTF-8")}

    def tearDown(self) -> None:
        s.execute("DELETE FROM course")
        s.commit()
        s.execute("DELETE FROM user")
        s.commit()

    def testAddCourse(self):
        addCourseUrl = '/course'
        self.student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        self.lector_id = int(self.client.post('/auth/register', json=self.test_lector).json.get('id'))

        test_course_correct = {
            "courseName": self.course_name,
            "courseDescription": "ksfdjfdslkj",
            "courseLector": self.lector_id
        }
        test_course_incorrect_owner = {
            "courseName": self.course_name,
            "courseDescription": "ksfdjfdslkj",
            "courseLector": self.student_id
        }
        self.assertEqual(400, self.client.post(addCourseUrl, headers=self.auth_lector_headers, json={}).status_code)
        self.assertEqual(403, self.client.post(addCourseUrl, headers=self.auth_student_headers, json={}).status_code)
        self.assertEqual(406, self.client.post(addCourseUrl, headers=self.auth_lector_headers, json=test_course_incorrect_owner).status_code)
        self.assertEqual(422, self.client.post(addCourseUrl, headers=self.auth_lector_headers, json={"field": "value"}).status_code)
        self.assertEqual(200, self.client.post(addCourseUrl, headers=self.auth_lector_headers, json=test_course_correct).status_code)

    def testGetCourse(self):
        courseUrl = '/course'
        self.student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        self.lector_id = int(self.client.post('/auth/register', json=self.test_lector).json.get('id'))

        test_course_correct = {
            "courseName": self.course_name,
            "courseDescription": "ksfdjfdslkj",
            "courseLector": self.lector_id
        }

        course_id = int(self.client.post(courseUrl, headers=self.auth_lector_headers, json=test_course_correct).json.get('id'))
        self.assertEqual(404, self.client.get(courseUrl+f'/{course_id+1000}', headers=self.auth_lector_headers).status_code)
        self.assertEqual(200, self.client.get(courseUrl+f'/{course_id}', headers=self.auth_lector_headers).status_code)

    def testDeleteCourse(self):
        courseUrl = '/course'
        self.student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        self.lector_id = int(self.client.post('/auth/register', json=self.test_lector).json.get('id'))

        test_course_correct = {
            "courseName": self.course_name,
            "courseDescription": "ksfdjfdslkj",
            "courseLector": self.lector_id
        }

        course_id = int(self.client.post(courseUrl, headers=self.auth_lector_headers, json=test_course_correct).json.get('id'))
        self.assertEqual(404, self.client.delete(courseUrl + f'/{course_id + 1000}',
                                              headers=self.auth_lector_headers).status_code)
        self.assertEqual(200, self.client.delete(courseUrl + f'/{course_id}', headers=self.auth_lector_headers).status_code)

    def testUpdateCourse(self):
        courseUrl = '/course'
        self.student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        self.lector_id = int(self.client.post('/auth/register', json=self.test_lector).json.get('id'))

        test_course_correct = {
            "courseName": self.course_name,
            "courseDescription": "ksfdjfdslkj",
            "courseLector": self.lector_id
        }
        new_course = {
            "courseName": self.course_name,
            "courseDescription": "other description",
            "courseLector": self.lector_id
        }
        new_course_incorrect_lector = {
            "courseName": self.course_name,
            "courseDescription": "other description",
            "courseLector": self.lector_id+1000
        }

        course_id = int(self.client.post(courseUrl, headers=self.auth_lector_headers, json=test_course_correct).json.get('id'))
        self.assertEqual(404, self.client.put(courseUrl+f'/{course_id+1000}', headers=self.auth_lector_headers, json={}).status_code)
        self.assertEqual(400, self.client.put(courseUrl+f'/{course_id}', headers=self.auth_lector_headers, json={}).status_code)
        self.assertEqual(422, self.client.put(courseUrl+f'/{course_id}', headers=self.auth_lector_headers, json={"field": "value"}).status_code)
        self.assertEqual(404, self.client.put(courseUrl+f'/{course_id}', headers=self.auth_lector_headers, json=new_course_incorrect_lector).status_code)
        self.assertEqual(200, self.client.put(courseUrl+f'/{course_id}', headers=self.auth_lector_headers, json=new_course).status_code)

    def testGetCourseByUserId(self):
        courseUrl = '/user/course'
        self.student_id = int(self.client.post('/auth/register', json=self.test_student).json.get('id'))
        self.lector_id = int(self.client.post('/auth/register', json=self.test_lector).json.get('id'))

        test_course_correct = {
            "courseName": self.course_name,
            "courseDescription": "ksfdjfdslkj",
            "courseLector": self.lector_id
        }
        self.assertEqual(404, self.client.get(courseUrl, headers=self.auth_lector_headers).status_code)
        self.client.post('/course', headers=self.auth_lector_headers, json=test_course_correct)
        self.client.post('/course', headers=self.auth_lector_headers, json=test_course_correct)
        self.client.post('/course', headers=self.auth_lector_headers, json=test_course_correct)
        self.assertEqual(200, self.client.get(courseUrl, headers=self.auth_lector_headers).status_code)
        self.assertEqual(403, self.client.get(courseUrl, headers=self.auth_student_headers).status_code)
