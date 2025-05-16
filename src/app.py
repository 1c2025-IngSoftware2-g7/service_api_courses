import os
from flask import Flask
from flask_cors import CORS

# Importing the blueprints..
from endpoints.courses import courses_bp
from endpoints.modules import modules_bp
from endpoints.user_endpoints import courses_enrollment_bp, users_approvation_bp
from endpoints.favourite_courses import courses_favourites
from endpoints.assistants import courses_assistants
from endpoints.feedbacks import feedbacks_bp


# Lets start the courses app by default on /courses
courses_app = Flask(__name__)

CORS(courses_app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Session config
courses_app.secret_key = os.getenv("SECRET_KEY_SESSION")


@courses_app.get("/courses/health")
def health_check():
    return {"status": "ok"}, 200


courses_app.register_blueprint(courses_bp)
courses_app.register_blueprint(modules_bp)
courses_app.register_blueprint(courses_enrollment_bp)
courses_app.register_blueprint(courses_favourites)
courses_app.register_blueprint(courses_assistants)
courses_app.register_blueprint(feedbacks_bp)
courses_app.register_blueprint(users_approvation_bp)

print(courses_app.url_map)
