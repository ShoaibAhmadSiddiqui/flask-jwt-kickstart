from flask import Flask
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from flask import request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from models import db, User
from helper import get_password_hash, verify_password
import os

load_dotenv()

app = Flask(__name__)
jwt = JWTManager(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, os.getenv("DB_NAME")
)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

db.init_app(app)


@app.route("/")
def hello():
    return "Hello world"


@app.cli.command("db_create")
def create_database():
    db.create_all()
    print("Database created!")


@app.cli.command("db_drop")
def drop_database():
    db.drop_all()
    print("Database dropped!")


@app.cli.command("db_seed")
def create_test_user():
    # Create a test user
    test_user = User(
        firstname="Shoaib",
        lastname="Ahmad",
        email="shoaib@example.com",
        password=get_password_hash("P@ssw0rd"),
    )

    db.session.add(test_user)
    db.session.commit()
    print("Database seeded!")


@app.route("/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify(message="Missing request body"), 400

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not (user and verify_password(password, user.password)):
        return jsonify(message="Bad email or password"), 401

    access_token = create_access_token(identity=email)
    return jsonify(status="success", access_token=access_token)


@app.route("/register", methods=["POST"])
def register():
    if not request.is_json:
        return jsonify(status="error", error="Missing request body"), 400

    data = request.get_json()
    email = data.get("email")
    if User.query.filter_by(email=email).first():
        # The email already exists in database
        return jsonify(status="error", error="Email already exists"), 409

    firstname = data.get("firstname", "")
    lastname = data.get("lastname", "")
    password = data.get("password")

    if email and password:
        # Create a new user
        user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=get_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(status="success", message="User created successfully."), 201

    return jsonify(status="error", error="Missing required data"), 400


@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    return jsonify(status="success")


if __name__ == "__main__":
    app.run()
