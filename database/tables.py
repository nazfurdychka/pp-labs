from sqlalchemy import Column, ForeignKey, Integer, Enum, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:password@localhost:3306/online_courses", echo=True)

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(45), nullable=False, unique=True)
    firstName = Column(String(45), nullable=False)
    lastName = Column(String(45), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(2000), nullable=False)
    phone = Column(String(45), nullable=True)
    userType = Column(Enum("Student", "Lector"), nullable=False)

    def __repr__(self):                                                                                                                         # pragma: no cover
        return f"{self.id}, {self.username}, {self.firstName}, {self.lastName}, {self.email}, " \
               f"{self.password}, {self.phone}, {self.userType}"


class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    courseName = Column(String(150), nullable=False)
    courseDescription = Column(String(500), nullable=False)
    courseLector = Column(Integer, ForeignKey("user.id"), nullable=False)

    User = relationship("User")

    def __repr__(self):                                                                                                                         # pragma: no cover
        return f"{self.id}, {self.courseName}, {self.courseDescription}, {self.courseLector}"


class Request(Base):
    __tablename__ = 'request'

    id = Column(Integer, primary_key=True)
    studentId = Column(Integer, ForeignKey("user.id"), nullable=False)
    requestToCourse = Column(Integer, ForeignKey("course.id"), nullable=False)
    requestToLector = Column(Integer, ForeignKey("user.id"), nullable=False)
    status = Column(Enum("OnHold", "Accepted", "Declined"), nullable=False, default="OnHold")

    User = relationship("User", foreign_keys=[studentId])
    User_lector = relationship("User", foreign_keys=[requestToLector])
    Course = relationship("Course", foreign_keys=[requestToCourse])

    def __repr__(self):                                                                                                                         # pragma: no cover
        return f"{self.id},{self.studentId} ,{self.requestToCourse}, {self.requestToLector}, {self.status}"


class CourseMember(Base):
    __tablename__ = 'courseMember'

    id = Column(Integer, primary_key=True)
    courseId = Column(Integer, ForeignKey("course.id"), nullable=False)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False)

    User = relationship("User")
    Course = relationship("Course")

    def __repr__(self):                                                                                                                         # pragma: no cover
        return f"{self.id}, {self.courseId}, {self.userId}"
