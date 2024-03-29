from typing import Text
import uuid
import os

from flask import Flask, request, render_template, redirect, make_response, url_for, session, flash, make_response, jsonify
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.functions import user
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
from models import User, Project, Task, Categoryes, Board, Sprint
from models import Connect_Categoryes, Connections_User_Project, Connections_User_Task, Connections_Sprint_User, Connections_Task_Sprint, Connections_Board_Categoryes

login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = "SECRET_KEY"
app.config.from_pyfile('config.cfg')

mail = Mail(app)

s = URLSafeTimedSerializer('Thisisasecret!')

init_db()


with app.app_context():
    print("HERE")

    category1 = Categoryes(name="Java")
    category2 = Categoryes(name="C++")
    category3 = Categoryes(name="C#")
    category4 = Categoryes(name="Python")
    category5 = Categoryes(name="Javascript")
    category6 = Categoryes(name="C")
    category7 = Categoryes(name="Other")

    category1_check = Categoryes.query.filter_by(name="Java").first()
    if not category1_check:
        db_session.add(category1)
        db_session.commit()

    category2_check = Categoryes.query.filter_by(name="C++").first()
    if not category2_check:
        db_session.add(category2)
        db_session.commit()

    category3_check = Categoryes.query.filter_by(name="C#").first()
    if not category3_check:
        db_session.add(category3)
        db_session.commit()

    category4_check = Categoryes.query.filter_by(name="Python").first()
    if not category4_check:
        db_session.add(category4)
        db_session.commit()

    category5_check = Categoryes.query.filter_by(name="Javascript").first()
    if not category5_check:
        db_session.add(category5)
        db_session.commit()

    category6_check = Categoryes.query.filter_by(name="C").first()
    if not category6_check:
        db_session.add(category6)
        db_session.commit()

    category7_check = Categoryes.query.filter_by(name="Other").first()
    if not category7_check:
        db_session.add(category7)
        db_session.commit()






ma = Marshmallow(app)
login_manager.init_app(app)


class TaskSchema(ma.Schema):
    class Meta:
        fields = ('id', 'project_id', 'taskname',
                  'description', 'completedate', 'state','importance')

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/invite/<int:project_id>/<username>')
@login_required
@check_confirmed
def invite(project_id,username):
    project = Project.query.filter_by(id=project_id).first()
    if project.admin_id != current_user.id:
        return redirect(url_for('index'))

    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("There is no such user", "danger")
        return redirect(url_for('search_for_colaborator', project_id=project_id))

    con = Connections_User_Project.query.filter_by(project_id=project_id, user_id=user.id).first()
    if con:
        flash("This user is already colaborator", "danger")
        return redirect(url_for('search_for_colaborator', project_id=project_id))

    token = s.dumps([project_id,username], salt='add-col')
    msg = Message('Invitation', sender='kanban.tues@abv.bg', recipients=[user.email])
    link = url_for('check_invite', token=token, _external=True)
    msg.body = '{} has invited you to colab in their project. The invite link is {}'.format(current_user.username, link)
    mail.send(msg)
    flash('The invitation has been send.', 'success')
    return redirect(url_for('show_project', project_id=project_id))

@app.route('/invite_sprint/<int:sprint_id>/<username>')
@login_required
@check_confirmed
def invite_sprint(sprint_id,username):
    sprint = Sprint.query.filter_by(id=sprint_id).first()
    project = Project.query.filter_by(id=sprint.project_id).first()
    user = User.query.filter_by(username=username).first()
    conUP = Connections_User_Project().query.filter_by(user_id=user.id,project_id=project.id).first()
    if conUP:
        conSP = Connections_Sprint_User.query.filter_by(user_id=user.id,sprint_id=sprint.id).first()
        if not conSP:
            new_conSP = Connections_Sprint_User(sprint_id=sprint.id, user_id=user.id)
            db_session.add(new_conSP)
            db_session.commit()
    return redirect(url_for('show_sprint', project_id=project.id,sprint_id=sprint.id))

@app.route('/check_invite/<token>')
@login_required
@check_confirmed
def check_invite(token):
    try:
        invite = s.loads(token, salt='add-col', max_age=3600)
        print(invite)
    except SignatureExpired:
        flash('The link is invalid or has expired.', 'danger')
        return '<h1>The token is expired!</h1>'

    user = User.query.filter_by(username=invite[1]).first()
    project = Project.query.filter_by(id=invite[0]).first()
    if user is None:
        flash('user There has been an error please ask for new invite.', 'danger')
        return redirect(url_for('index'))
    if project is None:
        flash('project There has been an error please ask for new invite.', 'danger')
        return redirect(url_for('index'))

    con = Connections_User_Project.query.filter_by(project_id=project.id, user_id=user.id).first()
    if con:
        flash("You are already colaborator", "danger")
        return redirect(url_for('index'))
    if current_user.id != user.id:
        flash('The invitation is invalid because of not maching identities', 'danger')
        return redirect(url_for('index'))
    conection = Connections_User_Project(user_id=user.id, project_id=project.id)
    db_session.add(conection)
    db_session.commit()

    flash("You have been added as colaborator", "success")
    return redirect(url_for('index'))

# @app.route('/_livesearch_in_project/<int:project_id>')
# @login_required
# @check_confirmed
# def livesearch_in_project(project_id):
#     text = request.args.get('text', type=str)

#     search = f"%{text}%"
#     print(search)
#     users = User.query.filter(User.username.like(search)).all()

#     result = []
#     for user in users:
#         if user.id != current_user.id:
#             con = Connections_User_Project.query.filter_by(user_id=user.id, project_id=project_id).first()
#             if con:
#                 result.append(user)


#     class JsonUser:
#         def __init__(self, id, username, email, name):
#             self.id = id
#             self.name = name
#             self.username = username
#             self.email = email

#         def to_json(self):
#             return self.__dict__

#     result = [JsonUser(r.id, r.username, r.email, r.name).to_json() for r in result]

#     print(result)

#     return jsonify(result)

@app.route('/_livesearch')
@login_required
@check_confirmed
def livesearch():
    text = request.args.get('text', type=str)

    search = f"%{text}%"
    print(search)
    users = User.query.filter(User.username.like(search)).all()

    result = {user for user in users if user.id != current_user.id}

    class JsonUser:
        def __init__(self, id, username, email, name):
            self.id = id
            self.name = name
            self.username = username
            self.email = email

        def to_json(self):
            return self.__dict__

    result = [JsonUser(r.id, r.username, r.email, r.name).to_json() for r in result]

    print(result)

    return jsonify(result)

@app.route("/sprint_serach_coll/<int:sprint_id>")
@login_required
@check_confirmed
def sprint_serach_coll(sprint_id):
    sprint = Sprint.query.filter_by(id=sprint_id).first()
    return render_template("add_user_to_sprint.html",sprint=sprint)

@app.route("/search_for_colaborator/<int:project_id>")
@login_required
@check_confirmed
def search_for_colaborator(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project.admin_id != current_user.id:
        return redirect(url_for('index'))
    return render_template("add_colaborator.html",project=project)

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
            user = User(username=username, password=generate_password_hash(password), email=email, name=name, confirmed=True)

            #send_token(email)

            db_session.add(user)
            db_session.commit()

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
    msg = Message('Confirm Email', sender='nov_meil_tues@abv.bg', recipients=[email])
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
def logout():
    current_user.login_id = None
    db_session.commit()
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgotPassword', methods=["GET", "POST"])
def forgotPassword():
    if request.method == 'GET':
        return render_template("forgotPassword.html")
    else:
        user = User.query.filter_by(email=request.form["email"]).first()
        subject = "Password reset requested"
        token = s.dumps(user.email, salt='recover-key')

        msg = Message(subject, sender='kanban.tues@abv.bg', recipients=[user.email])
        link = url_for('reset_with_token', token=token, _external=True)
        msg.body = 'Your link is {}'.format(link)
        mail.send(msg)
        return render_template('check_email.html')

@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        email = s.loads(token, salt="recover-key", max_age=3600)
    except:
        flash('The link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))

    user = User.query.filter_by(email=email).first()
    if request.method == 'POST':
        new_pass = request.form["new_pass"]
        new_pass_conf = request.form["conf_new_pass"]
        if new_pass == new_pass_conf:
            user.password = generate_password_hash(new_pass)

            db_session.add(user)
            db_session.commit()
    else:
        return render_template("recover_password.html")
    return redirect(url_for('login'))

@app.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        email = s.loads(token, salt='email-confirm')
        user = User.query.filter_by(email=email).first()
        db_session.delete(user)
        db_session.commit()
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

        conection = Connections_User_Project(user_id=current_user.id, project_id=project.id)
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
    con = Connections_User_Project.query.filter_by(project_id=project.id, user_id=current_user.id).first()
    if con is None:
        flash("You are not a colaborator to this porject", "danger")
        return redirect(url_for('index'))
    else:
        assigned = {}
        not_assigned = {}
        connectionUT = {}
        task_catt = {}
        user_sprints = []
        all_tasks = Task.query.filter_by(project_id=project_id).order_by(Task.importance).all()
        result = tasks_schema.dump(all_tasks)
        users_in_project = Connections_User_Project.query.filter_by(project_id=project_id).all()
        users_id_in_project = []
        user_boards = []

        for u in users_in_project:
            users_id_in_project.append(u.user_id)

        for i in all_tasks:
            connection = Connections_User_Task.query.filter_by(task_id=i.id).all()
            categories_task = Connect_Categoryes.query.filter_by(task_id=i.id).all()
            categories = []
            names = []
            user_id = []
            other_names = []
            non_assign_ids = users_id_in_project

            for c in categories_task:
                cat = Categoryes.query.filter_by(id=c.categoryes_id).first()
                categories.append(cat.name)

            for conn in connection:
                user_id.append(conn.user_id)

            for u in user_id:
                non_assign_ids.remove(u)
                user = User.query.filter_by(id=u).first()
                names.append(user.username)

            for u_id in non_assign_ids:
                if u_id != current_user.id:
                    user = User.query.filter_by(id=u_id).first()
                    other_names.append(user.username)

            task_catt[i.id] = categories
            assigned[i.id] = names
            not_assigned[i.id] = other_names
            c = Connections_User_Task.query.filter_by(task_id=i.id, user_id=current_user.id).first()
            if c:
                connectionUT[i.id] = False
            else:
                connectionUT[i.id] = True

        spirnts = Sprint.query.filter_by(project_id=project_id).all()
        boards = Board.query.filter_by(project_id=project_id).all()
        for i in spirnts:
            is_connect = Connections_Sprint_User.query.filter_by(sprint_id=i.id, user_id=current_user.id).first()
            if is_connect:
                user_sprints.append(i)

        for i in boards:
            user_boards.append(i)



        return render_template("project.html",result=result, project=project, spirnts=user_sprints, conUT=connectionUT, assigned=assigned, not_assigned=not_assigned, boards=user_boards, task_catt=task_catt)

@app.route('/assign_task/<int:task_id>/<username>')
@login_required
@check_confirmed
def assign_task(task_id,username):
    user = User.query.filter_by(username=username).first()
    task = Task.query.filter_by(id=task_id).first()
    project = Project.query.filter_by(id=task.project_id).first()
    conUP = Connections_User_Project().query.filter_by(user_id=user.id,project_id=project.id).first()
    if conUP:
        conection = Connections_User_Task(task_id=task.id, user_id=user.id)
        db_session.add(conection)
        db_session.commit()
        flash("Task assigned", "success")
        return redirect(url_for('show_project', project_id=project.id))
    flash("Task not assigned", "danger")
    return redirect(url_for('index'))

@app.route('/unassign_task/<int:task_id>')
@login_required
@check_confirmed
def unassign_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    project = Project.query.filter_by(id=task.project_id).first()
    conUP = Connections_User_Task().query.filter_by(user_id=current_user.id, task_id=task_id).first()
    if conUP:
        db_session.delete(conUP)
        db_session.commit()
        flash("Task unassigned", "success")
        return redirect(url_for('show_project', project_id=project.id))
    flash("Error", "danger")
    return redirect(url_for('index'))

@app.route('/project_sprint/<int:project_id>/<int:sprint_id>')
@login_required
@check_confirmed
def show_sprint(project_id,sprint_id):
    sprint = Sprint.query.filter_by(id=sprint_id).first()
    project = Project.query.filter_by(id=project_id).first()
    con = Connections_User_Project.query.filter_by(project_id=project.id, user_id=current_user.id).first()

    if con is None:
        flash("You are not colaborator", "danger")
        return redirect(url_for('index'))
    if sprint.project_id != project_id:
        flash("No such sprint", "danger")
        return redirect(url_for('index'))
    else:
        all_tasks_con = Connections_Task_Sprint.query.filter_by(sprint_id=sprint_id).all()
        all_tasks = []
        for t in all_tasks_con:
            task = Task.query.filter_by(id=t.task_id).first()
            print("task = ")
            print(task)
            all_tasks.append(task)
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

        return render_template("sprint.html",update_todo = to_do, update_progress = progress, update_testing = testing, update_done = done, project=project, sprint=sprint)

@app.route('/create_sprint/<int:project_id>', methods=['GET', 'POST'])
@login_required
@check_confirmed
def create_sprint(project_id):
    if request.method == "POST":
        project = Project.query.filter_by(id=project_id).first()
        if project:
            sprint_name = request.form["sprint_name"]
            completedate = datetime.strptime(request.form['sprint_completedate'], '%Y-%m-%d')
            sprint = Sprint(name=sprint_name,project_id=project_id,completedate=completedate)
            db_session.add(sprint)
            db_session.commit()

            conection = Connections_Sprint_User(user_id=current_user.id, sprint_id=sprint.id)
            db_session.add(conection)
            db_session.commit()
            flash("Sprint added successfully!","success")
            return redirect(url_for('show_project', project_id=project_id))
        else:
            flash("Non such project","danger")
            return redirect(url_for('index'))

@app.route('/create_board/<int:project_id>', methods=['GET', 'POST'])
@login_required
@check_confirmed
def create_board(project_id):
    if request.method == "POST":
        project = Project.query.filter_by(id=project_id).first()
        if project:
            board_name = request.form["board_name"]
            categories = request.form.getlist("category")
            board = Board(name=board_name,project_id=project_id,user_id=current_user.id)
            db_session.add(board)
            db_session.commit()

            curr_board = Board.query.filter_by(name=board_name,project_id=project_id,user_id=current_user.id).first()

            for i in categories:
                curr_cat = Categoryes.query.filter_by(name=i).first()

                if curr_cat:
                    connection = Connections_Board_Categoryes(board_id=curr_board.id, categoryes_id=curr_cat.id)
                    db_session.add(connection)
                    db_session.commit()

            tasks = Task.query.filter_by()
            flash("Board created successfully!","success")
            return redirect(url_for('show_project', project_id=project_id))
        else:
            flash("Non such project","danger")
            return redirect(url_for('index'))

@app.route('/board_project/<int:project_id>/<int:board_id>')
@login_required
@check_confirmed
def show_board(project_id,board_id):
    board = Board.query.filter_by(id=board_id).first()
    project = Project.query.filter_by(id=project_id).first()
    con = Connections_User_Project.query.filter_by(project_id=project.id, user_id=current_user.id).first()

    if con is None:
        flash("You are not colaborator", "danger")
        return redirect(url_for('index'))
    if board.project_id != project_id:
        flash("No such board", "danger")
        return redirect(url_for('index'))
    else:
        conBC = Connections_Board_Categoryes.query.filter_by(board_id=board_id).all()
        all_tasks_con = Connect_Categoryes.query.filter_by(categoryes_id=conBC[0].categoryes_id).all()
        categories = []

        for i in conBC:
            curr = Categoryes.query.filter_by(id=i.categoryes_id).first()
            categories.append(curr)
            for connection in all_tasks_con:
                con = Connect_Categoryes.query.filter_by(task_id=connection.task_id,categoryes_id=i.categoryes_id).first()

        #all_tasks_con = Connections_Task_Sprint.query.filter_by(sprint_id=sprint_id).all()

        all_tasks = []
        for t in all_tasks_con:
            task = Task.query.filter_by(id=t.task_id).first()
            print("task = ")
            print(task)
            all_tasks.append(task)
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

        return render_template("board.html",update_todo = to_do, update_progress = progress, update_testing = testing, update_done = done, project=project, board=board, categories=categories)


@app.route('/add_task_sprint/<task_id>/<project_id>', methods=['GET', 'POST'])
@login_required
@check_confirmed
def add_task_sprint(task_id, project_id):
    sprints = Sprint.query.filter_by(project_id=project_id).all()
    if request.method == "POST":
        sprint_name = request.form['sprint_name']
        sprint = Sprint.query.filter_by(name=sprint_name).first()
        if sprint:
            scon = Connections_Task_Sprint.query.filter_by(task_id=task_id,sprint_id=sprint.id).first()
            if scon:
                flash("Task already in sprint", "success")
                return redirect(url_for('show_project', project_id=project_id))
            conection = Connections_Task_Sprint(task_id=task_id,sprint_id=sprint.id)
            db_session.add(conection)
            db_session.commit()
            print("here")
            flash("Task added to sprint", "success")
        return redirect(url_for('show_project', project_id=project_id))
    return render_template("add_task_sprint.html", sprints=sprints)

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
    taskstate = request.form['taskstate']
    importance = request.form['importance']
    categories = request.form.getlist('category')
    print(categories)

    new_task = Task(project_id=project_id, taskname=taskname, description=description, completedate=completedate, state=taskstate, importance=importance)
    db_session.add(new_task)
    db_session.commit()

    curr_task = Task.query.filter_by(project_id=project_id, taskname=taskname, description=description, completedate=completedate, state=taskstate, importance=importance).first()
    for i in categories:
        category = Categoryes.query.filter_by(name=i).first()
        if category:
            connection_t_c = Connect_Categoryes(task_id=curr_task.id, categoryes_id=category.id)
            db_session.add(connection_t_c)
            db_session.commit()
            flash("Task created", "success")
        else:
            db_session.delete(curr_task)
            db_session.commit()
            flash("Task not created", "danger")

    return redirect(url_for('show_project', project_id=project_id))

@app.route('/move_task/<task_id>/<state>/<project_id>/<int:sprint_id>/<int:board_id>', methods=['GET'])
@login_required
@check_confirmed
def move_task(task_id, state, project_id, sprint_id, board_id):
    task = Task.query.get(task_id)
    task.state = state

    db_session.commit()
    if sprint_id == 0:
        return redirect(url_for('show_board', project_id=project_id,board_id=board_id))
    else:
        return redirect(url_for('show_sprint', project_id=project_id,sprint_id=sprint_id))

@app.route('/delete_task/<task_id>/<project_id>', methods=['GET'])
@login_required
@check_confirmed
def delete_task(task_id, project_id):
    task = Task.query.get(task_id)
    conTCat = Connect_Categoryes.query.filter_by(task_id=task.id).all()
    for i in conTCat:
        db_session.delete(i)

    conTU = Connections_User_Task.query.filter_by(task_id=task.id).all()
    for i in conTU:
        db_session.delete(i)

    conTS = Connections_Task_Sprint.query.filter_by(task_id=task.id).all()
    for i in conTS:
        db_session.delete(i)
     
    db_session.delete(task)
    db_session.commit()

    return redirect(url_for('show_project', project_id=project_id))

@app.route('/',methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        if current_user.confirmed == 1:
            con = Connections_User_Project.query.filter_by(user_id = current_user.id).all()
            projects = []
            for c in con:
                projects += Project.query.filter_by(id = c.project_id).all()
            return render_template("index.html",projects = projects)
        else:
            return redirect(url_for('unconfirmed'))
    else:
        return render_template("index_for_non_users.html")
