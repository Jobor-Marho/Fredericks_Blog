from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from datetime import datetime
from notification_manager import NotificationManager
from formats import MONTHS, POSITION
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from dotenv.main import load_dotenv
import os


load_dotenv()
date = datetime.now()
current_day = date.day
current_month = MONTHS[f"{date.month}"]
current_year = date.year
logged_in = False
error = None

my_app = Flask(__name__)
my_app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

ckeditor = CKEditor(my_app)
Bootstrap(my_app)
login_manager = LoginManager(my_app)

my_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
my_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(my_app)
gravatar = Gravatar(my_app, size=50, rating='g', default='retro', force_default=False, force_lower=False,
                    use_ssl=False, base_url=None)


def get_feed():
    return db.session.query(BlogPost).all()


# Users Database
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    # Parent relationship of BlogPost
    posts = db.relationship('BlogPost', back_populates='author', lazy=True)
    # Parent relationship of Comment
    comments = db.relationship('Comment', back_populates='comment_author', lazy=True)




# Blog database
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # Child relationship to User
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.relationship('User', back_populates='posts')

    body = db.Column(db.Text, nullable=False)

    # Parent relationship of Comment
    # blog_comments = db.relationship('Comment', back_populates='parent_post')
    comments = db.relationship('Comment', back_populates='current_blogpost', lazy=True)

    date = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    # Child Relationship of User
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_author = db.relationship('User', back_populates='comments')
    comment_text = db.Column(db.String(250))
    date = db.Column(db.String(250))
    # Child Relationship to BlogPost
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    current_blogpost = db.relationship('BlogPost', back_populates='comments')

with my_app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@my_app.route("/")
def get_homepage():
    global logged_in
    feed = get_feed()
    return render_template("index.html", day=current_day, month=current_month, year=current_year, feed=feed,
                           current_user=current_user, logged_in=logged_in)


@my_app.route("/about")
def get_about():
    global logged_in
    return render_template("about.html", day=current_day, month=current_month, year=current_year, logged_in=logged_in)


@my_app.route("/contact", methods=['POST', 'GET'])
def get_contact():
    global logged_in
    if request.method == "POST":
        name = request.form['Name']
        email = request.form['Email']
        phone = request.form['Phone']
        message = request.form['Message']
        msg = f"Name: {name}\nEmail: {email}\nPhone Number: {phone}\nMessage: {message}"
        notify = NotificationManager(msg=msg, recipient="imlearning862@gmail.com", subject="Blog Message")
        if notify:
            success_msg = "Successfully, sent your message."
            return render_template("contact.html", day=current_day, month=current_month, year=current_year, success=True,
                                   success_msg=success_msg, logged_in=logged_in)
        else:
            return render_template('error.html')
    return render_template("contact.html", day=current_day, month=current_month,
                           year=current_year, success=False, logged_in=logged_in)


@my_app.route('/delete-blogpost/<int:index>')
@login_required
def delete(index):
    feed = get_feed()
    post = feed[index]
    db.session.delete(post)
    db.session.commit()
    return redirect('/')


@my_app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def edit(post_id):
    global logged_in
    feed = get_feed()
    post = db.session.query(BlogPost).filter_by(id=feed[post_id].id).first()

    form = CreatePostForm(
                            title=post.title,
                            subtitle=post.subtitle,
                            img_url=post.img_url,
                            body=post.body
                        )
    if request.method == "POST":
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.img_url = form.img_url.data
        post.body = form.body.data
        db.session.commit()
        return redirect(f'/post/{post_id}')

    return render_template('make-post.html', edit=True, form=form, logged_in=logged_in)


@my_app.route('/login', methods=['POST', 'GET'])
def login():
    global logged_in, error
    form = LoginForm()
    if request.method == 'POST':
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        try:
            user_password = user.password
        except AttributeError:
            error = "This email does not exist. Please try again."
            redirect(url_for('login'))
        else:
            if check_password_hash(pwhash=user_password, password=password):
                login_user(user)
                error = None
                logged_in = True
                return redirect(url_for("get_homepage"))
            else:
                error = "Incorrect password. Please try again."
                redirect(url_for('login'))
    return render_template("login.html", form=form, logged_in=logged_in, error=error)


@my_app.route('/logout')
def logout():
    global logged_in, error
    logout_user()
    error = None
    logged_in = False
    return redirect('/')


@my_app.route("/new-post", methods=['GET', 'POST'])
@login_required
def create_post():
    global logged_in
    form = CreatePostForm()
    if request.method == "POST":
        new_post = BlogPost(title=form.title.data,
                            subtitle=form.subtitle.data,
                            author=current_user,
                            img_url=form.img_url.data,
                            body=form.body.data,
                            date=f"{current_month} {current_day}, {current_year}"
                            )

        db.session.add(new_post)
        db.session.commit()
        return redirect("/")

    return render_template("make-post.html", form=form, edit=False, logged_in=logged_in)


@my_app.route("/post/<int:id>", methods=['POST', 'GET'])
def get_post(id):
    day = [digit for digit in str(current_day)]
    global logged_in, error
    form = CommentForm()
    feed = get_feed()
    if request.method == 'POST':
        if not logged_in:
            error = 'Please Login to post a comment.'
            return redirect('/login')
        comment = form.comment.data
        new_comment = Comment()
        new_comment.comment_text = comment
        new_comment.comment_author = current_user
        new_comment.current_blogpost = feed[id]
        if current_day == 12 or current_day == 13:
            new_comment.date = f"{current_day}th/{current_month}/{current_year}"
        else:
            new_comment.date = f"{current_day}{POSITION[day[-1]]}/{current_month}/{current_year}"
        db.session.add(new_comment)
        db.session.commit()

        return redirect(f'/post/{id}')
    return render_template("post.html", day=current_day, month=current_month, year=current_year, title=feed[id].title,
                           subtitle=feed[id].subtitle, body=feed[id].body, img_url=feed[id].img_url,
                           author=feed[id].author.name, date=feed[id].date, id=id, current_user=current_user,
                           logged_in=logged_in, form=form, comments=feed[id].comments)


@my_app.route('/register', methods=['POST', 'GET'])
def register():
    global error, logged_in
    form = RegisterForm()
    if request.method == "POST":
        # Check to see if you can find the email of the new user if it exists
        user = User.query.filter_by(email=form.email.data).first()
        try:
            email = user.email
        except AttributeError:
            new_user = User()
            new_user.name = form.name.data
            new_user.email = form.email.data
            password_hash = generate_password_hash(password=form.password.data, salt_length=8)
            new_user.password = password_hash
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            error = None
            logged_in = True
            if new_user.id == 1 and get_feed() == []:
                return redirect('/new-post')
            else:
                return redirect('/')
        else:
            error = 'Sorry that email has already been registered. Login Instead'
            return redirect('login')
    return render_template("register.html", form=form, error=error)


if __name__ == "__main__":
    my_app.run(host='0.0.0.0:$PORT', port=5000)
