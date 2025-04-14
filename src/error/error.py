from flask import jsonify


def error_generator(message, detail, code, instance):
    return {
        "response": jsonify(
            {
                "type": "about:blank",
                "title": message,
                "status": 0,
                "detail": detail,
                "instance": f"/courses/" + instance,
            }
        ),
        "code_status": code,
    }
