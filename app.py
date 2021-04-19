import uuid
import os

from flask import Flask, request, render_template, redirect, make_response, url_for, session, flash, make_response
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import asc
from flask_marshmallow import Marshmallow
from datetime import datetime
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


from decorators import check_confirmed
from database import db_session, init_db
from models import User, Project, Task, Connections

login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = "SECRET_KEY"
app.config.from_pyfile('config.cfg')

mail = Mail(app)

s = URLSafeTimedSerializer('Thisisasecret!')

init_db()

ma = Marshmallow(app)
login_manager.init_app(app)


class TaskSchema(ma.Schema):
    class Meta:
        fields = ('id', 'project_id', 'taskname',
                  'description', 'completedate', 'state')


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
        password = request.form["password"]
        confirm_pasword = request.form["verify_password"]
        email = request.form["email"]
        
        user = User.query.filter_by(username=username).first()
        if(user is not None):
            flash("This username already exists!", "danger")
            return render_template("register.html")
        user = User.query.filter_by(email=email).first()
        if(user is not None):
            flash("This email is already in use!", "danger")
            return render_template("register.html")

        if confirm_pasword == password:
            user = User(username=username, password=generate_password_hash(password), email=email, name=name, confirmed=False)

            db_session.add(user)
            db_session.commit()

            send_token(email)

            user.login_id = str(uuid.uuid4())
            db_session.commit()
            login_user(user)
            flash('You registered and are now logged in. Welcome!', 'success')
            return redirect(url_for('unconfirmed'))
            #return render_template("go_confirm.html", email = email)
        else:
            
            flash("Passwords doesn`t match!","danger")

    return render_template("register.html")

@app.route('/resend', methods=['GET', 'POST'])
def resend():
    send_token(current_user.email)
    return redirect(url_for('unconfirmed'))

def send_token(email):
    token = s.dumps(email, salt='email-confirm')
    msg = Message('Confirm Email', sender='kanban.project.tues@gmail.com', recipients=[email])
    link = url_for('confirm_email', token=token, _external=True)
    msg.body = 'Your link is {}'.format(link)
    mail.send(msg)


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
            return redirect(url_for('unconfirmed'))
        else:
            flash("Wrong username or password!","danger")
            return redirect(url_for('login'))

@app.route('/logout')
@login_required
@check_confirmed
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    print("HERE")
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return '<h1>The token is expired!</h1>'

    user = User.query.filter_by(email=email).first()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        db_session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('index'))   

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('index'))
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@check_confirmed
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


@app.route('/create_project', methods=['GET', 'POST'])
@login_required
@check_confirmed
def create_project():
    if request.method == "POST":
        project_name = request.form["name"]
        description = request.form["description"]

        project = Project(project_name=project_name, description=description, admin_id=current_user.id)
        db_session.add(project)
        db_session.commit()

        conection = Connections(user_id=current_user.id, project_id=project.id)
        db_session.add(conection)
        db_session.commit()
        
        flash("Project added successfully!","success")
        return redirect(url_for('index'))
    return render_template("create_project.html")

@app.route('/project/<int:project_id>')
@login_required
@check_confirmed
def show_project(project_id):
    project = Project.query.filter_by(id=project_id).first()

    if project.admin_id != current_user.id:
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
@login_required
@check_confirmed
def add_task(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project.admin_id != current_user.id:
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
@login_required
@check_confirmed
def move_task(task_id, state,project_id):
    task = Task.query.get(task_id)
    task.state = state

    db_session.commit()
    return redirect(url_for('show_project', project_id=project_id))


@app.route('/delete_task/<task_id>/<project_id>', methods=['GET'])
@login_required
@check_confirmed
def delete_task(task_id, project_id):
    task = Task.query.get(task_id)
    db_session.delete(task)
    db_session.commit()

    return redirect(url_for('show_project', project_id=project_id))

@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if current_user.confirmed == 1:
            con = Connections.query.filter_by(user_id = current_user.id).all()
            projects = []
            for c in con:
                projects += Project.query.filter_by(id = c.project_id).all()
            return render_template("index.html",projects = projects)
        else:
            return redirect(url_for('unconfirmed'))
    else:
        return render_template("index_for_non_users.html")
