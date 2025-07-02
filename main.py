from flask import Flask,render_template, request,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationship
from sqlalchemy import Integer, String, Float,ForeignKey
from datetime import datetime
from flask_login import login_user,LoginManager,logout_user,login_required,UserMixin,current_user
from werkzeug.security import generate_password_hash, check_password_hash

# from forms import TaskForm

app=Flask(__name__)

class Base(DeclarativeBase):
    pass
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///tasks.db"
app.config["SECRET_KEY"]="this_is_a_todo_list_app"
db=SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager=LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))

class User(db.Model,UserMixin):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    username:Mapped[str]=mapped_column(String(100))
    password:Mapped[str]=mapped_column(String(100))
    tasks=relationship('Tasks',back_populates="user")


class Tasks(db.Model):
    __tablename__="task_list"
    id:Mapped[int]=mapped_column(Integer, primary_key=True)
    task:Mapped[str]=mapped_column(String(250),nullable=False)
    due_date:Mapped[str]=mapped_column(String(250),nullable=False)
    status:Mapped[str]=mapped_column(String(250),nullable=False)
    completion_date:Mapped[str]=mapped_column(String(250),nullable=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"))
    user=relationship("User",back_populates="tasks")

with app.app_context():
    db.create_all()

@app.route("/",methods=["GET","POST"])
def home_page():
    if request.method=="POST":
        if not current_user.is_authenticated:
            flash("You need to log in to add tasks.")
            return redirect(url_for("login"))
        task=request.form.get('task')
        due_date=request.form.get('due_date')
        new_task=Tasks(
            task=task,
            due_date=due_date,
            status="incomplete",
            user_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
    if current_user.is_authenticated:

        all_tasks=db.session.execute(db.select(Tasks).where(Tasks.user_id==current_user.id)).scalars().all()
        
    else:
        all_tasks=[]
        
    all_tasks.reverse()
    return render_template('tasks.html',tasks=all_tasks)

@app.route("/status/<int:task_id>",methods=["GET","POST"])
def status_update(task_id):
    completion_date=datetime.now().strftime("%m-%d-%Y")
    task=db.get_or_404(Tasks,task_id)
    task.status="complete"
    task.completion_date=completion_date
    db.session.commit()
    
    return redirect(url_for('home_page'))

@app.route("/delete/<int:task_id>",methods=["GET","POST"])
def delete_task(task_id):
    task=db.get_or_404(Tasks, task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home_page'))

@app.route("/login",methods=["POST","GET"])
def login():
    email=request.form.get("email")
    password=request.form.get("password")
    user=db.session.execute(db.select(User).where(User.email==email)).scalar()
    
    if user:
        if check_password_hash(user.password,password):
            login_user(user)
            
            return redirect(url_for("home_page"))
        else:
            flash("Incorrect Password","danger")
            return redirect(url_for("home_page"))

    else:
        flash("Email not found","danger")
        return redirect(url_for("home_page"))

@app.route("/logout",methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    
    return redirect(url_for("home_page"))



@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method=="POST":
        email=request.form.get("email")
        username=request.form.get("username")
        password=request.form.get("password")
        hash_and_salted_password=generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user=User(
            email=email,
            username=username,
            password=hash_and_salted_password
        )
        already_their=db.session.execute(db.select(User).where(User.email==email)).scalar()
        if already_their:
            flash("Already have a account ! Log in instead","danger")
            return redirect(url_for("login"))
        else:
            db.session.add(new_user)
            db.session.commit()
        
            login_user(new_user)

            return redirect(url_for('home_page'))




if __name__=="__main__":
    app.run(debug=False)