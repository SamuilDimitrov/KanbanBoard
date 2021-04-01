import uuid
import os

from flask import Flask, request, render_template, redirect, make_response, url_for, session, flash, make_response
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import asc
from flask_marshmallow import Marshmallow
from datetime import datetime

from database import db_session, init_db
from models import User, Board, Company, Task, Connections

login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = "Thisissecret"


init_db()
'''
com = Company(name="Unemployed", address="Home")
db_session.add(com)
db_session.commit()
'''
ma = Marshmallow(app)
login_manager.init_app(app)

class TaskSchema(ma.Schema):
    class Meta:
        fields = ('id','project_id','taskname', 'description', 'completedate','state')

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        username = request.form["username"]
        name = request.form["name"]
        company = Company.query.filter_by(name=request.form["company"]).first()
        password = request.form["password"]
        confirm_pasword = request.form["verify_password"]
        user = User.query.filter_by(username=username).first()
        if(user is not None):
            flash("This username already exists!","danger")
            return render_template("register.html")
        if confirm_pasword == password:
            user = User(username=username, password=generate_password_hash(password), name=name, company_id=company.id)
            db_session.add(user)
            db_session.commit()
            flash("Registration complete!","success")
            return redirect(url_for('login'))
        else:
            flash("Passwords doesn`t match!","danger")

    companyes = Company.query.all()
    return render_template("register.html", companyes = companyes)

@app.route('/joinCompany', methods=['GET', 'POST'])
@login_required
def joinCompany():
	if request.method == "POST":
			company = Company.query.filter_by(name=request.form["company"]).first()
			username = current_user.username
			user = User.query.filter_by(username=username).first()
			if check_password_hash(company.password, request.form["password"]):
				user.company_id = company.id
				db_session.commit()
				flash("Company joined!","success")
				return redirect(url_for('profile'))
			else:
				flash("Passwords doesn't match!","danger")
				return redirect(url_for('joinCompany'))
	companyes = Company.query.all()
	return render_template("joinCompany.html", companyes = companyes)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	if request.method == "POST":
		username = request.form["username"]
		user = User.query.filter_by(username=username).first()
		password = request.form["password"]
		if check_password_hash(current_user.password, request.form["password"]):
			if(user is not None):
				flash("This username already exists!","danger")
				return render_template("profile.html")
			current_user.username = username
			current_user.name = request.form["name"]
			db_session.commit()
			flash("Profile Updated!","success")
			return redirect(url_for('profile'))
		else:
			flash("Wrong password!","danger")
			return redirect(url_for('profile'))
	else:
		return render_template("profile.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template("login.html")
    else:

        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            flash("You are logged in!","success")
            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Wrong username or password!","danger")
            return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()
    return redirect(url_for('login'))
    
@app.route('/forgotPassword')
def forgotPassword():
	return render_template("forgotPassword.html")

@app.route('/registerCompany', methods=['GET', 'POST'])
@login_required
def registerCompany():
    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]
        password = request.form["password"]
        confirm_pasword = request.form["verify_password"]
        company = Company.query.filter_by(name=name).first()
        if(company is not None):
            flash("This Company already exists!","danger")
        else:
            if confirm_pasword == password:
                company_to_create = Company(name=name, password=generate_password_hash(password), address=address, admin_id=current_user.id)
                db_session.add(company_to_create)
                db_session.commit()
                flash("Registration complete!","success")
                return redirect(url_for('profile'))
            else:
                flash("Passwords doesn`t match!","danger")
    return render_template("registerCompany.html")

@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == "POST":
        project_name = request.form["name"]
        description = request.form["description"]
        project = Board(project_name=project_name, description=description, company_id=current_user.company_id)
        db_session.add(project)
        db_session.commit()
        flash("Project added successfully!","success")
        return redirect(url_for('index'))
    return render_template("create_project.html")

@app.route('/project/<int:project_id>')
@login_required
def show_project(project_id):
    project = Board.query.filter_by(id=project_id).first()

    if project.company_id != current_user.company_id:
        return redirect(url_for('login'))
    else:
        all_tasks = Task.query.filter_by(project_id=project_id).all()
        result = tasks_schema.dump(all_tasks)
        
        to_do = []
        progress = []
        testing = []
        done = []
        
        for i in result:
            if datetime.strptime(i['completedate'][:10], '%Y-%m-%d') > datetime.today():
                i['overdue'] = False
            else:
                i['overdue'] = True
            if i['state'] == 'TO DO':
                to_do.append(i)
            elif i['state'] == 'PROGRESS':
                progress.append(i)
            elif i['state'] == 'TESTING':
                testing.append(i)
            else:
                done.append(i)
                
        return render_template("project.html",update_todo = to_do, update_progress = progress, update_testing = testing, update_done = done, project=project)

@app.route('/add_task/<int:project_id>', methods=['GET', 'POST'])
def add_task(project_id):
    project = Board.query.filter_by(id=project_id).first()
    if project.company_id != current_user.company_id:
        return redirect(url_for('login'))

    taskname = request.form['taskname']
    description = request.form['description']
    completedate = datetime.strptime(request.form['completedate'], '%Y-%m-%d')
    taskstate = request.form['taskcategory']

    new_task = Task(project_id=project_id, taskname=taskname, description=description, completedate=completedate, state=taskstate)

    db_session.add(new_task)
    db_session.commit()

    return redirect(url_for('show_project', project_id=project_id))

@app.route('/move_task/<task_id>/<state>/<project_id>', methods=['GET'])
def move_task(task_id, state,project_id):
    task = Task.query.get(task_id)
    task.state = state

    db_session.commit()
    return redirect(url_for('show_project', project_id=project_id))


@app.route('/delete_task/<task_id>/<project_id>', methods=['GET'])
def delete_task(task_id, project_id):
    task = Task.query.get(task_id)
    db_session.delete(task)
    db_session.commit()

    return redirect(url_for('show_project', project_id=project_id))

@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        projects = Board.query.filter_by(company_id = current_user.company_id).all()
        return render_template("index.html",projects = projects)
    else:
        return render_template("index_for_non_users.html")
