from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql.expression import func
from datetime import datetime


from database import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(200), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    name = Column(String(200), nullable=False)
    login_id = Column(String(36), nullable=True)
    confirmed = Column(Boolean, nullable=False, default=False)
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.login_id

    def is_confirmed(self):
        return confirmed

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    project_name = Column(String(80), unique=True, nullable=False)# уникално име според компания
    description = Column(String(1000), nullable=True)
    admin_id = Column(Integer, ForeignKey('user.id'))
    #company_id = Column(Integer, ForeignKey('company.id'), nullable = False)

'''
class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    address = Column(String(200), unique=True, nullable=False)
    admin_id = Column(Integer, ForeignKey('user.id'))
    password = Column(String(120))
'''

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    taskname = Column(String(1000), nullable=False)
    description = Column(String(1000), nullable=True)
    completedate = Column(DateTime)
    state = Column(Enum('TO DO','PROGRESS','TESTING','DONE'))

class Categoryes(Base):
    __tablename__ = 'categoryes'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

class ConnectCategoryes(Base):
    __tablename__ = 'connectcategoryes'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'))
    technology_id = Column(Integer, ForeignKey('categoryes.id'))

class Connections(Base):
    __tablename__ = 'connections'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('task.id'))
