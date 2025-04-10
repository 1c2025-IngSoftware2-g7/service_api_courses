import logging
import os
from flask import Flask, request


courses_app = Flask(__name__)

# Session config
courses_app.secret_key = os.getenv("SECRET_KEY_SESSION")


@courses_app.get("/health")
def health_check():
    return {"status": "ok"}, 200

