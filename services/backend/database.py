from datetime import datetime
from pathlib import Path
import pymongo
import os
import shutil

from helper import generate_sha1_hex, get_current_timestamp, save_image, download_image

user = os.environ.get("MONGO_USERNAME")
password = os.environ.get("MONGO_PASSWORD")
host = "mongodb:27017"


class Database:
    def __init__(self):
        db_name = "playstore"
        connection_uri = f'mongodb://{user}:{password}@{host}/?authSource=admin'
        # connection_uri = f'mongodb://{host}/?authSource=admin'

        client = pymongo.MongoClient(connection_uri)

        db = client[db_name]

        self.application = db["application"]

        self.version = db["version"]

        self.files = db["files"]

        self.users = db["users"]

        self.downloads = Path('/downloads')

        self.base_url = os.environ.get("DOMAIN_BASE_URL")

    def _get_application_by_package(self, package_name):

        apps = list(self.application.find({"package_name": package_name}))

        return apps

    def search_applications(self, keyword, limit):

        apps = list(self.application.find(
            {
                "title": {
                    "$regex": keyword,
                    '$options': 'i'
                }
            }
        ).limit(limit))

        return apps

    def add_application(self, data):

        package_name = data["package_name"]

        apps = self._get_application_by_package(package_name)

        if len(apps) > 0:
            return False, apps[0]["_id"], "we already have this app in our database"

        id = generate_sha1_hex(package_name)

        data["_id"] = id
        data["created_at"] = get_current_timestamp()
        data["updated_at"] = get_current_timestamp()
        data["status"] = "scraping"
        data["error_count"] = 0

        url = data["icon_url"]

        content = download_image(url)
        if content != None:
            folder = self.downloads.joinpath(id)
            filename = folder.joinpath("icon.png")
            save_image(folder, filename, content)

        self.application.insert_one(data)
        return True, id, "application added into database."

    def delete_application(self, package_id):
        status = False
        message = "all application data is deleted"
        try:
            self.files.delete_many(
                {"package_id": package_id}
            )

            self.version.delete_many(
                {
                    "package_id": package_id
                }
            )

            self.application.delete_one(
                {
                    "_id": package_id
                }
            )

            # delete folder

            folder_path = self.downloads.joinpath(package_id)

            shutil.rmtree(folder_path)
            status = True
        except Exception as e:
            message = str(e)
            status = False

        return status, message

    def update_application(self, package_id, data):
        data["updated_at"] = get_current_timestamp()
        self.application.update_one(
            {"_id": package_id},
            {
                "$set": data
            }
        )

    def get_latest_app(self, package_name, blog_url, download_link_expire_seconds, token_generator):
        data = {}
        tmp = {}
        data["package_name"] = package_name
        apps = list(self.application.find(
            {"package_name": package_name, "status": "active"}))

        if len(apps) == 0:
            tmp["app_status"] = False
            tmp["data"] = data
            return tmp

        tmp["app_status"] = True

        app = apps[0]

        data["app_name"] = app["title"]
        data["mode_type"] = "No"

        files = list(self.files.find({"package_id": app["_id"],"status":"active"}).sort(
            "published_on_timestamp", pymongo.DESCENDING))

        if len(files) == 0:
            tmp["version_status"] = False
            return tmp
        tmp["version_status"] = True

        file = files[0]
        apk_type = file["apk_type"]
        data["file_type"] =apk_type
        data["file_size"] = file["size_text"]
        data["version_number"] = file["version"]

        data["last_updated"] = file["published_on_timestamp"].strftime(
            "%B %d,%Y").title()

        tmp_data = {
            "download_filename": file["filename"] + "." + apk_type,
            "folder_name": app["_id"],
            "server_file_name": file["version_unique_id"] + "." + apk_type,
            "download_link_expire_seconds": download_link_expire_seconds
        }

        if blog_url != None:
            tmp_data["redirect"] = blog_url

        download_token = token_generator.generate_ttl_token(tmp_data)

        data["download_url"] = f'{self.base_url}/api/download/' + \
            download_token

        tmp["data"] = data

        return tmp

    def get_recent_application(self, limit):
        tmp = {}

        apps = list(
            self.application.find({}).sort(
                "updated_at", pymongo.DESCENDING).limit(limit)
        )

        tmp["total_apps"] = self.application.count_documents({})
        tmp["apps"] = apps
        return tmp

    def _get_application_by_package_id(self, package_id):
        apps = list(self.application.find({"_id": package_id}))
        return apps

    def get_application_details(self, package_id):

        app = self._get_application_by_package_id(package_id)

        if len(app) == 0:
            return False, None

        application_details = app[0]

        application_files = list(self.files.find({"package_id": package_id}).sort(
            "published_on_timestamp", pymongo.DESCENDING))

        application_details["files"] = application_files

        return True, application_details

    def add_file(self, data):
        data["created_at"] = get_current_timestamp()
        data["updated_at"] = get_current_timestamp()
        try:
            self.files.insert_one(data)
            return True
        except:
            return False
