from flask import Flask, render_template, url_for, redirect,session,request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import UserMixin, LoginManager, login_required, logout_user, current_user, login_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource, abort, reqparse, marshal_with, fields
from flask_cors import CORS
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import csv
import sqlite3
from datetime import datetime
# ....................................    __initializing app__  ........................................................


app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tododb.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
api = Api(app)
cors = CORS(app)
# ....................................... __Creating Login FrameWork__ ..................................................


login_Manager = LoginManager()
login_Manager.init_app(app)
login_Manager.login_view = "login"

@login_Manager.user_loader 
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    
    def get_id(self):
        return (self.user_id)

    def __repr__(self):
        return "< User %r>" % self.username


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Username"})

    password = PasswordField(validators=[InputRequired(), Length(min=4, max=8)], render_kw={"placeholder":"Password"})

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()

        if existing_user_username:
            raise ValidationError("Username Already Exists!! Try another one")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder":"Username"})

    password = StringField(validators=[InputRequired(), Length(min=4, max=8)], render_kw={"placeholder":"Password"})

    submit = SubmitField("Login")  

#.......................................   __Creating Database Models__  ....................................................


class Todo(db.Model):
    todo_id = db.Column(db.Integer, primary_key = True)
    todo_user = db.Column(db.String(20), nullable = False)
    todo_name = db.Column(db.String(20), nullable = False)
    Todolist = db.relationship("listform", backref = "todo", secondary = 'association')

class listform(db.Model):
    list_id = db.Column(db.Integer, primary_key=True)
    listName= db.Column(db.String(30), unique = True)
    Description = db.Column(db.String(100), nullable = False)
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())
    def __repr__(self):
        return "< listform %r>" % self.listName

list_args = reqparse.RequestParser()
list_args.add_argument("listName", type = str, required = True)
list_args.add_argument("Description", type = str)

list_output_fields = {
    'list_unique_id' : fields.Integer(attribute = "list_id"),
    "listName" : fields.String,
    "Description" : fields.String
}

class Association(db.Model):
    todo_id = db.Column(db.Integer(),db.ForeignKey('todo.todo_id'), primary_key = True)

    list_id = db.Column(db.Integer(), db.ForeignKey('listform.list_id'), primary_key = True)


class Card(db.Model):
    card_id = db.Column(db.Integer, primary_key = True)
    list = db.Column(db.String(), nullable = False)
    title = db.Column(db.String(), nullable = False, unique = True)
    content = db.Column(db.String(100), nullable = False)
    deadline = db.Column(db.String, nullable = False)
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())
card_args = reqparse.RequestParser()
card_args.add_argument("list", type = str, required = True)
card_args.add_argument("title", type = str, required = True)
card_args.add_argument("content", type = str, required = True)
card_args.add_argument("deadline", type = str, required = True)

card_output_fields = {
    "card_unique_id" : fields.Integer(attribute = "card_id"),
    "list" : fields.String,
    "title" : fields.String,
    "content" : fields.String,
    "deadline" : fields.String,
}

class CardStat(db.Model):
    cardstat_id = db.Column(db.Integer, primary_key = True)
    cardstat_name = db.Column(db.String(30), nullable = False)
    cardstat_complete = db.Column(db.Integer, nullable = False)
    cardstat_dailyhours = db.Column(db.Integer, nullable = False)
    cardstat_approx = db.Column(db.Integer, nullable = False)
    cardstat_rate = db.Column(db.Integer, nullable = False)
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())

class Status(db.Model):
    card = db.Column(db.String(), primary_key = True)
    Pending = db.Column(db.Integer())
    Complete = db.Column(db.Integer())
    Incomplete = db.Column(db.Integer())
    Less_than_50 = db.Column(db.Integer())
    More_than_50 = db.Column(db.Integer())
#....................................  __API and ROUTES for CRUD and Functionality__  ..........................................

class listRc(Resource):
    @marshal_with(list_output_fields)
    def get(self, id):
        li = listform.query.filter_by(list_id = id).first()
        if li :
            return li, 200
        else:
            abort(404, message = "list doesn't found/exist")

    def post(self):
        args = list_args.parse_args()
        check = args.get("listName", None)
        if check == None:
            return {"error_code" : "list0001",
            'error_message' : "No listName in the request"}, 400
        li = listform.query.filter_by(listName = args["listName"]).first()
        if li :
            abort(409, message = "listName already Exists !")
        else:
            list = listform(listName = args['listName'], Description = args['Description'])
            db.session.add(list)
            db.session.commit()
            return{
                'list_id' : list.list_id,
                'listName' : list.listName,
                'Description' : list.Description
            }, 201

    def delete(self, id):
        li = listform.query.filter_by(list_id = id).first()
        if li:
            db.session.delete(li)
            db.session.commit()
            return "list Successfully deleted", 200
        else:
            abort(404, message = "list doesn't exist")

    def put(self, id):
        li = listform.query.filter_by(list_id = id).first()
        
        args = list_args.parse_args()
        li.listName = args['listName']
        li.Description = args['Description']
        db.session.add(li)
        db.session.commit()
        
        return{
            'list_id' : li.list_id,
            'listName' : li.listName,
            'Description' : li.Description
        }, 201
        
class cardRc(Resource):
    @marshal_with(card_output_fields)
    def get(self, id):
        Ca = Card.query.filter_by(card_id = id).first()
        if Ca :
            return Ca, 200
        else:
            abort(404, message = "Card doesn't found/exist")

    def post(self):
        args = card_args.parse_args()
        check = args.get("list", None)
        if check == None:
            return {"error_code" : "Card0001",
            'error_message' : "No cardName in the request"}, 400
        Ca = Card.query.filter_by(list = args["list"]).first()
        if Ca :
            abort(409, message = "CardName already Exists !")
        else:
            card = Card(list = args['list'],  title = args['title'], content = args['content'], deadline = args['deadline'])
            db.session.add(card)
            db.session.commit()
            return{
                "card_list" : card.list,
                "card_title" : card.title,
                "card_content" : card.content,
                "card_deadline" : card.deadline,
            }, 201

    def delete(self, id):
        Ca = Card.query.filter_by(card_id = id).first()
        if Ca:
            db.session.delete(Ca)
            db.session.commit()
            return "Card Successfully deleted", 200
        else:
            abort(404, message = "Card doesn't exist")

    def put(self, id):
        Ca = Card.query.filter_by(card_id = id).first()
        
        args = card_args.parse_args()
        Ca.list = args['list']
        Ca.title = args['title']
        Ca.content = args['content']
        Ca.deadline = args['deadline']
        db.session.add(Ca)
        db.session.commit()
        
        return{
            "card_list" : Ca.list,
            "card_title" : Ca.title,
            "card_content" : Ca.content,
            "card_deadline" : Ca.deadline,
        }, 201

api.add_resource(listRc, "/api/list" , "/api/list/<int:id>")
api.add_resource(cardRc, "/api/card", "/api/card/<int:id>")


# ------------------------------------------- Routes Controllers --------------------------------------------------


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('Kanbanboard'))
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hassed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hassed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))       

    return render_template('register.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/Addlist',methods=['GET','POST'])
@login_required
def Addlist():
    if request.method == 'GET':
        return render_template('listform.html')
   
@app.route('/kanbanboard', methods=['GET'])
@login_required
def kanban():
    if request.method == 'GET':
            allTodo = listform.query.all()
            cards = Card.query.all()
            cardstat = CardStat.query.all()
            return render_template('kanbanboard.html', allTodo = allTodo, cards=cards, cardstat = cardstat)

@app.route('/Kanbanboard', methods=['GET', 'POST'])
@login_required
def Kanbanboard():
    if request.method == 'GET':
            allTodo = listform.query.all()
            cards = Card.query.all()
            cardstat = CardStat.query.all()
            return render_template('kanbanboard.html', allTodo = allTodo, cards=cards, cardstat = cardstat)
    if request.method == 'POST':
        new_list = request.form.get('addlist')
        new_desc = request.form.get('description')
        data = listform(listName = new_list , Description = new_desc)
        db.session.add(data)
        db.session.commit()
        u1 = Todo(todo_user = current_user.username, todo_name = new_list)
        db.session.add(u1)
        db.session.commit()
        u1.Todolist.append(data)
        db.session.commit()
        allTodo = listform.query.all()
        cards = Card.query.all()
        cardstat = CardStat.query.all()
        return render_template('kanbanboard.html', allTodo = allTodo, cards=cards, cardstat = cardstat)
        
   

@app.route('/update/<int:list_id>', methods=['GET' , 'POST'])
@login_required
def update(list_id):
    if request.method == 'GET':
        todo = listform.query.filter_by(list_id=list_id).first()
        return render_template('update.html', todo=todo)
    if request.method == 'POST':
        new_list = request.form.get('addlist')
        new_desc = request.form.get('description')
        todo = listform.query.filter_by(list_id=list_id).first()
        todos = Todo.query.filter_by(todo_name = todo.listName).first()

        todo.listName = new_list
        todo.Description = new_desc
        todos.todo_name = new_list

        db.session.add(todo)
        db.session.commit()
        db.session.add(todos)
        db.session.commit()

        return redirect(url_for("Kanbanboard"))
    

@app.route('/Delete/<int:list_id>')
@login_required
def delete(list_id):
    todo = listform.query.filter_by(list_id=list_id).first()
    todos = Todo.query.filter_by(todo_name = todo.listName).first()
    cardstatdelete = CardStat.query.filter_by(cardstat_name = todo.listName).first()
    try:

        db.session.delete(cardstatdelete)
    except:
        pass
    else:
        pass

    db.session.commit()
    db.session.delete(todos)
    db.session.commit()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("Kanbanboard"))

@app.route('/Delete/<title>')
@login_required
def card_delete(title):
    todo_d = Card.query.filter_by(title=title).first()
    db.session.delete(todo_d)
    db.session.commit()
    try:
        CardStatus = Status.query.filter_by(card = title).first()
        db.session.delete(CardStatus)
        db.session.commit()
    except:
        pass
    return redirect(url_for("Kanbanboard"))


@app.route('/updatecard/<int:card_id>', methods=['GET' , 'POST'])
@login_required
def updatecard(card_id):
    if request.method == 'GET':
        alltodo = Todo.query.all()
        card = Card.query.filter_by(card_id=card_id).first()
        return render_template('updatecard.html', card=card, alltodo=alltodo)
    if request.method == 'POST':
        list = request.form.get('list')
        title = request.form.get('title')
        content = request.form.get('content')
        deadline = request.form.get('deadline')

        date_out = datetime(*[int(v) for v in deadline.replace('T', '-').replace(':', '-').split('-')])

        todocard = Card.query.filter_by(card_id=card_id).first()

        todocard.list = list
        todocard.title = title
        todocard.content = content
        todocard.deadline = date_out
        db.session.add(todocard)
        db.session.commit()

        status = request.form.get('status')
        StatusCard = Status.query.filter_by(card = title).first()
        if status == "Pending":
            StatusCard.Pending = 30
            StatusCard.Complete = 0
            StatusCard.Incomplete = 0
            StatusCard.Less_than_50 = 0
            StatusCard.More_than_50 = 0
        elif status == "Complete":
            StatusCard.Pending = 0
            StatusCard.Complete = 100
            StatusCard.Incomplete = 0
            StatusCard.Less_than_50 = 0
            StatusCard.More_than_50 = 0
        elif status == "Incomplete":
            StatusCard.Pending = 0
            StatusCard.Complete = 0
            StatusCard.Incomplete = 0
            StatusCard.Less_than_50 = 0
            StatusCard.More_than_50 = 0
        elif status == "less50":
            StatusCard.Pending = 0
            StatusCard.Complete = 0
            StatusCard.Incomplete = 0
            StatusCard.Less_than_50 = 20
            StatusCard.More_than_50 = 0
        elif status == "more50":
            StatusCard.Pending = 0
            StatusCard.Complete = 0
            StatusCard.Incomplete = 0
            StatusCard.Less_than_50 = 0
            StatusCard.More_than_50 = 80

        db.session.add(StatusCard)
        db.session.commit()
        return redirect(url_for("Kanbanboard"))


@app.route('/cardlist', methods=['GET', 'POST'])
@login_required
def cardlist():
    if request.method == 'GET':
        alltodo = Todo.query.all()
        return render_template('cardlist.html',alltodo = alltodo)

    if request.method == 'POST':
        list = request.form.get('list')
        title = request.form.get('title')
        content = request.form.get('content')
        deadline = request.form.get('deadline')

        date_out = datetime(*[int(v) for v in deadline.replace('T', '-').replace(':', '-').split('-')])

        data = Card(list = list, title = title, content = content, deadline = date_out)
        db.session.add(data)
        db.session.commit()

        status = request.form.get('status')
        if status == "Pending":
            Pending = 30
            Complete = 0
            Incomplete = 0
            less50 = 0
            more50 = 0
        elif status == "Completed":
            Pending = 0
            Complete = 100
            Incomplete = 0
            less50 = 0
            more50 = 0
        elif status == "Incomplete":
            Pending = 0
            Complete = 0
            Incomplete = 0
            less50 = 0
            more50 = 0
        elif status == "less50":
            Pending = 0
            Complete = 0
            Incomplete = 0
            less50 = 20
            more50 = 0
        elif status == "more50":
            Pending = 0
            Complete = 0
            Incomplete = 0
            less50 = 0
            more50 = 80
        else:
            pass
            
        dataNXT = Status(card = title, Pending = Pending, Complete = Complete, Incomplete = Incomplete, Less_than_50 = less50, More_than_50 = more50)
        db.session.add(dataNXT)
        db.session.commit()

        return redirect(url_for('Kanbanboard'))


@app.route('/cards' , methods=['GET'])
@login_required
def cards():
    allcard = Card.query.all()
    allTodo = listform.query.all()
    return render_template('card.html', allcard=allcard, allTodo = allTodo)

@app.route('/summary', methods=['GET','POST'])
@login_required
def summary():
    if request.method == 'GET':
        cardstat = CardStat.query.all()
        allTodo = listform.query.all()
        status = Status.query.all()
        cardgraph = Card.query.all()
        return render_template('summary.html', cardstat = cardstat, allTodo = allTodo, status = status, cardgraph = cardgraph)

    if request.method == 'POST':
            cardstatname = request.form.get('list')
            taskcompleted=request.form.get('taskcompleted')
            dailyhours = request.form.get('dailyhours')
            approxtime = request.form.get('approxtime')
            ratework = request.form.get('ratework')
            data = CardStat(cardstat_name = cardstatname,cardstat_complete = taskcompleted, cardstat_dailyhours = dailyhours, cardstat_approx = approxtime, cardstat_rate = ratework)
            try:
                deletecard = CardStat.query.filter_by(cardstat_name = cardstatname).first()
                db.session.delete(deletecard)
            except:
                pass
            else:
                pass
            db.session.add(data)
            db.session.commit()
            cardstat = CardStat.query.all()
            allTodo = listform.query.all()
            status = Status.query.all()
            cardgraph = Card.query.all()
            return render_template('summary.html', cardstat = cardstat, allTodo = allTodo, status = status, cardgraph=cardgraph)

db.create_all()

@app.route('/import_list', methods=['GET','POST'])
@login_required
def import_list():
    conn = sqlite3.connect('tododb.db')
    cursor = conn.cursor()
    cursor.execute("select * from listform;")
    with open("list.csv", 'w',newline='') as csv_file: 
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([i[0] for i in cursor.description]) 
        csv_writer.writerows(cursor)
    conn.close()
    msg = "list.csv file has been generated check depository"
    return redirect(url_for("Kanbanboard", msg=msg))

@app.route('/import_Card', methods=['GET','POST'])
@login_required
def import_Card():
    conn = sqlite3.connect('tododb.db')
    cursor = conn.cursor()
    cursor.execute("select * from Card;")
    with open("card.csv", 'w',newline='') as csv_file: 
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([i[0] for i in cursor.description]) 
        csv_writer.writerows(cursor)
    conn.close()
    msg = "card.csv file has been generated check depository"
    return redirect(url_for("Kanbanboard", msg=msg))


#..............................................  __App Run__  ..........................................................

if __name__ == '__main__':
    app.run(debug=True)





