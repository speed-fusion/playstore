from genericpath import isdir
from pathlib import Path
import os
import pymongo
from datetime import datetime
import bson
import shutil
import zipfile

user = os.environ.get("MONGO_USERNAME")
password = os.environ.get("MONGO_PASSWORD")
host = "mongodb:27017"

class MongoDatabase:
    def __init__(self):
        db_name = "playstore"
        connection_uri = f'mongodb://{user}:{password}@{host}/?authSource=admin'
        client = pymongo.MongoClient(connection_uri)
        self.db = client[db_name]
        self.apps =  self.db["application"]
        self.files = self.db["files"]
    
    def get_all_collection(self):
        return list(self.db.list_collections())
    

class GenerateBackupZip:
    def __init__(self) -> None:
        
        self.db = MongoDatabase()
        
        self.cwd = Path.cwd()
        
        self.now = datetime.now()
        
        self.backup_dir = self.cwd.joinpath("backup")
        
        if not self.backup_dir.exists():
            self.backup_dir.mkdir()
        
        self.mongo_backup_dir = self.backup_dir.joinpath("MONGODB")
        
        if not self.mongo_backup_dir.exists():
            self.mongo_backup_dir.mkdir()
        
        self.zip_path = self.backup_dir.joinpath(self.now.strftime("cdn.onehost.io-%d_%m_%Y.zip"))
        
        self.downloads_dir = Path("/downloads")
        
        self.todays_zip = zipfile.ZipFile(self.zip_path,"w")

    def generate_mongodb_backup_zip(self):
        
        for collection in self.db.get_all_collection():
            file_path = self.mongo_backup_dir.joinpath(f'{collection["name"]}.bson')
            with open(file_path,'wb+') as f:
                for doc in self.db.db[collection["name"]].find({}):
                    f.write(bson.BSON.encode(doc))
            print(f'file generated : {file_path}')

            self.todays_zip.write(str(file_path),f'mongo_backup/{file_path.name}',zipfile.ZIP_DEFLATED)
            
            file_path.unlink()
        
        # tmp_mongo_zip_path = self.backup_dir.joinpath(self.now.strftime("MONGODB_%d_%m_%Y"))
        
        # shutil.make_archive(str(tmp_mongo_zip_path),'zip',str(self.mongo_backup_dir))
        
        # shutil.rmtree(str(self.mongo_backup_dir))
        
        # return self.mongo_zip_path
    
    def directory_iterator(self,target_dir:Path):
        for item in target_dir.glob("*"):
            if item.is_dir() == True:
                self.directory_iterator(item)
            else:
                print(f'found path : {item}')
                yield str(item)
    
    def generate_apk_backup_zip(self):
        
        for path in self.directory_iterator(self.downloads_dir):
            self.todays_zip.write(path,f'apk_backup/{path}',zipfile.ZIP_DEFLATED)
    
    
    # you can use this code to restore the database. you need to provide backup directory path and database instance.
    def restore_mongodb_backup_file(self,dir_path,db,db_name="playstore"):
        
        for collection in os.listdir(dir_path):
            if collection.endswith(".bson"):
                with open(os.path.join(dir_path,collection),'rb+') as f:
                    db[collection.split('.')[0]].insert_many(bson.decode_all(f.read()))
                    