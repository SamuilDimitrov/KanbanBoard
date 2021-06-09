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
        return self.confirmed

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    project_name = Column(String(80), unique=True, nullable=False)
    description = Column(String(1000), nullable=True)
    admin_id = Column(Integer, ForeignKey('user.id'))

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    taskname = Column(String(1000), nullable=False)
    description = Column(String(1000), nullable=True)
    completedate = Column(DateTime)
    state = Column(Enum('TO DO','PROGRESS','TESTING','DONE'))
    importance = Column(Enum('P0','P1','P2','P3','P4'))

class Board(Base):
    __tablename__ = 'board'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

class Sprint(Base):
    __tablename__ = 'sprint'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    completedate = Column(DateTime)

class Categoryes(Base):
    __tablename__ = 'categoryes'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

class Connect_Categoryes(Base):
    __tablename__ = 'connectcategoryes'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    categoryes_id = Column(Integer, ForeignKey('categoryes.id'), nullable=False)

class Connections_User_Project(Base):
    __tablename__ = 'connectionsuserproject'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)

class Connections_User_Task(Base):
    __tablename__ = 'connectionsusertask'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)

class Connections_Sprint_User(Base):
    __tablename__ = 'connectionssprintuser'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sprint_id = Column(Integer, ForeignKey('sprint.id'), nullable=False)

class Connections_Task_Sprint(Base):
    __tablename__ = 'connectionstasksprint'
    id = Column(Integer, primary_key=True)
    sprint_id = Column(Integer, ForeignKey('sprint.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)

class Connections_Board_Categoryes(Base):
    __tablename__ = 'connectionsboardcategoryes'
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey('board.id'), nullable=False)
    categoryes_id = Column(Integer, ForeignKey('categoryes.id'), nullable=False)