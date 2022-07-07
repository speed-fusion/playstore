from flask import Flask, Response, jsonify, redirect, request, send_from_directory
from database import Database
from flask_cors import CORS

from pathlib import Path
import shutil
from apkpure_scraper import ApkpureScraper
from ttl_token import TllToken
from datetime import datetime, timedelta


import json
import logging

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    JWTManager,
)

from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt


class JSONEncoder(json.JSONEncoder):
    ''' extend json-encoder class'''

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, set):
            return list(o)
        if isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)

CORS(app)

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


app.config["JWT_SECRET_KEY"] = "3bc27a33-ac7d-4f15-be44-2748de7c9d57"

app.config["JWT_TOKEN_LOCATION"] = ["headers"]

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365*100)

jwt = JWTManager(app)

flask_bcrypt = Bcrypt(app)
app.json_encoder = JSONEncoder


@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"auth": False}), 401


db = Database()

token_generator = TllToken()

scraper = ApkpureScraper()


@app.route('/auth', methods=['POST'])
def auth_user():
    ''' auth endpoint '''

    data = request.get_json()["data"]

    u = list(db.users.find({'email': data['email']}))

    if len(u) == 0:
        return jsonify({
            "status": False,
            "message": "the email address is invalid.",
            "data": None
        })

    user = u[0]

    pwd = user.get("password")

    if user and flask_bcrypt.check_password_hash(pwd, data['password']):
        del user['password']
        del data['password']
        access_token = create_access_token(identity=data)
        refresh_token = create_refresh_token(identity=data)
        user['token'] = access_token
        user['refresh'] = refresh_token
        return jsonify({'status': True, 'data': user}), 200
    else:
        return jsonify({'status': False, 'message': 'invalid password'}), 200


@app.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    ''' refresh token endpoint '''
    current_user = get_jwt_identity()
    ret = {
        'token': create_access_token(identity=current_user)
    }
    return jsonify({'ok': True, 'data': ret}), 200


@app.route('/register', methods=['POST'])
@jwt_required()
def register():
    ''' register user endpoint '''

    data = request.get_json()["data"]

    user = list(db.users.find({'email': data['email']}))

    if len(user) != 0:
        return jsonify({
            "status": False,
            "message": "user already exists.",
            "data": None
        })

    data['password'] = flask_bcrypt.generate_password_hash(data['password'])

    db.users.insert_one(data)

    return jsonify({'status': True, 'msg': 'User created successfully!'}), 200


# to get search suggestion from keyword

@app.route('/get-suggestion')
@jwt_required()
def get_suggestion():
    keyword = request.args.get("q")

    status, data = scraper.get_suggestions_v2(keyword)

    return jsonify({
        "data": data,
        "status": status
    })

# add application in database


@app.route('/add-application', methods=["POST"])
@jwt_required()
def add_application():
    data = request.json["data"]

    status, id, message = db.add_application(data)

    return jsonify({
        "status": status,
        "message": message,
        "data": {
            "_id": id
        }
    })


@app.route('/icon/<id>', methods=["GET"])
def fetch_icon(id):
    return send_from_directory(f'/downloads/{id}', "icon.png")


@app.route('/search-applications', methods=["GET"])
@jwt_required()
def search_applications():
    default_limit = 20
    limit = request.args.get("limit")
    if limit != None:
        default_limit = int(limit)

    keyword = request.args.get("keyword")

    data = db.search_applications(keyword, default_limit)

    return jsonify({
        "status": True,
        "message": "",
        "data": data
    })


@app.route('/delete-application', methods=["GET"])
@jwt_required()
def delete_application():
    package_id = request.args.get("package_id")

    status, message = db.delete_application(package_id)

    return jsonify({
        "status": status,
        "message": message
    })


@app.route('/update-application', methods=["POST"])
@jwt_required()
def update_application():
    package_id = request.args.get("package_id")

    data = request.json["data"]

    db.update_application(package_id, data)

    return jsonify({
        "status": True,
        "message": "data updated"
    }), 200


@app.route('/app-latest', methods=["POST"])
# @jwt_required()
def app_latest():
    data = request.get_json()["data"]

    package_name = data["package_name"]

    blog_url = data.get("blog_url", None)

    download_link_expire_seconds = data.get(
        "download_link_expire_seconds", 600)

    data = db.get_latest_app(package_name, blog_url,
                             download_link_expire_seconds, token_generator)

    return jsonify(data), 200


@app.route('/get-recent-application', methods=["GET"])
@jwt_required()
def get_recent_application():
    default_limit = 20

    limit = request.args.get("limit")

    if limit != None:
        default_limit = int(limit)

    recent_application = db.get_recent_application(default_limit)

    return jsonify({
        "status": True,
        "data": recent_application
    }), 200


@app.route('/get-application-details', methods=["GET"])
@jwt_required()
def get_application_details():
    package_id = request.args.get("package_id")

    status, app_details = db.get_application_details(package_id)

    for file in app_details["files"]:
        
        data = {
            "download_filename": file["filename"] + "." + file.get("apk_type",""),
            "folder_name": package_id,
            "server_file_name": file["version_unique_id"] + "." + file.get("apk_type","")
        }

        token = token_generator.generate_ttl_token(data)

        file["download_token"] = token

    return jsonify({
        "status": status,
        "data": app_details
    }), 200


@app.route('/download/<token>')
def download_file(token):

    data = token_generator.decode_ttl_token(token)
    app.logger.info(data)
    download_filename = data["download_filename"]
    folder_name = data["folder_name"]
    server_file_name = data["server_file_name"]

    
    if data["status"] == True:
        return send_from_directory(f'/downloads/{folder_name}', server_file_name, as_attachment=True, download_name=download_filename)
    else:
        return redirect(data["redirect"], code=302)


if __name__ == '__main__':
    app.run(debug=True)
