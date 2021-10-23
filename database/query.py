from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.tables import *

session = sessionmaker(bind=engine)
s = session()

new_user = User(username="Patsu.rar", firstName="sasha", lastName="patsuryn", email="example@mail.com",
                password="qwerty123", phone="+380565498549", userType="Lector")
new_user1 = User(username="Petrushka", firstName="Nazar", lastName="Hriyhir", email="example1@mail.com",
                 password="qwerty123", phone="+380565412349", userType="Student")
new_course = Course(courseName="Course 1", courseDescription="Description 1", courseLector=1)
new_course1 = Course(courseName="Course 2", courseDescription="Description 2", courseLector=1)
new_request = Request(requestToCourse=1, requestToLector=1, status="Accepted")
new_studentRequest = StudentRequest(requestId=1, userId=2)
new_courseMember = CourseMember(courseId=1, userId=2)

# s.add(new_user)
# s.add(new_user1)
# s.add(new_course)
# s.add(new_course1)
# s.add(new_request)
# s.add(new_studentRequest)
# s.add(new_courseMember)

s.commit()

# res = s.query(User).filter(User.id >= 0)
#
# for row in res:
#     print(row)
