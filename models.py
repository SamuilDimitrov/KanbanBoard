from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql.expression import func
from datetime import datetime
import enum

from database import Base

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(120), nullable=False)
    name = Column(String(200), nullable=False)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=True, default=1)
    login_id = Column(String(36), nullable=True)
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.login_id

class Board(Base):
    __tablename__ = 'board'
    id = Column(Integer, primary_key=True)
    project_name = Column(String(80), unique=True, nullable=False)
    description = Column(String(1000), nullable=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable = False)

class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    address = Column(String(200), unique=True, nullable=False)
    admin_id = Column(Integer, ForeignKey('user.id'))
    password = Column(String(120))

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('board.id'), nullable=False)
    task_name = Column(String(1000), nullable=False)
    description = Column(String(1000), nullable=True)
    date_created = Column(DateTime, default=datetime.now)
    state = Column(Enum('TO DO','PROGRESS','TESTING','DONE'))

class Connections(Base):
    __tablename__ = 'connections'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('board.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)