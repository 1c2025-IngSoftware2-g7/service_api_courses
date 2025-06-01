import os
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

# Importing the blueprints..
from endpoints.courses import courses_bp
from endpoints.tasks import tasks_bp
from endpoints.modules_and_resources import modules_bp, resources_bp
from endpoints.user_endpoints import courses_enrollment_bp, users_approvation_bp
from endpoints.favourite_courses import courses_favourites
from endpoints.assistants import courses_assistants
from endpoints.feedbacks import feedbacks_bp


# Lets start the courses app by default on /courses
courses_app = Flask(__name__)

CORS(courses_app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Session config
courses_app.secret_key = os.getenv("SECRET_KEY_SESSION")

# Swagger config
swagger_config = {
    "headers": [],
    "title": "Courses API",
    "version": "1.0.0",
    "description": "Courses API Documentation",
    "termsOfService": "",
    "specs_route": "/docs/",
    "static_url_path": "/flasgger_static",
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ]
}

Swagger(courses_app, config=swagger_config)

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
courses_app.register_blueprint(tasks_bp)
courses_app.register_blueprint(resources_bp)

print(courses_app.url_map)
