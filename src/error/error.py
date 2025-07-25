from flask import jsonify

def error_generator(message, detail, code, instance):
    from services.logger_config import get_logger
    logger = get_logger("api-courses")
    logger.error(f"/courses/{instance} {code} - {message}: {detail}")
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
