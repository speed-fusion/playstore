from pathlib import Path
import os
import pymongo
from datetime import datetime
import bson
import shutil


user = os.environ.get("MONGO_USERNAME")
password = os.environ.get("MONGO_PASSWORD")
host = "mongodb:27017"

class MongoDatabase:
    def __init__(self):
        db_name = "playstore"
        connection_uri = f'mongodb://{user}:{password}@{host}/?authSource=admin'
        client = pymongo.MongoClient(connection_uri)
        self.db = client[db_name]
    
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
        
        self.mongo_zip_path = self.backup_dir.joinpath(self.now.strftime("MONGODB_%d_%m_%Y.zip"))
        self.files_zip_path = self.backup_dir.joinpath(self.now.strftime("FILES_%d_%m_%Y.zip"))
            
        self.downloads_dir = Path("/downloads")
        
    def generate_mongodb_backup_zip(self):
        
        for collection in self.db.get_all_collection():
            file_path = self.current_date_dir.joinpath(f'{collection}.bson')
            with open(file_path,'wb+') as f:
                for doc in self.db.db[collection].find({}):
                    f.write(bson.BSON.encode(doc))
            print(f'file generated : {file_path}')
        
        shutil.make_archive(str(self.mongo_zip_path),str(self.mongo_backup_dir))
        
        shutil.rmtree(str(self.mongo_backup_dir))
        
        return self.mongo_zip_path
        
    def generate_apk_backup_zip(self):
        shutil.make_archive(str(self.files_zip_path),'zip',str(self.downloads_dir))
        
        return self.files_zip_path
    
    # you can use this code to restore the database. you need to provide backup directory path and database instance.
    def restore_mongodb_backup_file(self,dir_path,db,db_name="playstore"):
        
        for collection in os.listdir(dir_path):
            if collection.endswith(".bson"):
                with open(os.path.join(dir_path,collection),'rb+') as f:
                    db[collection.split('.')[0]].insert_many(bson.decode_all(f.read()))
                    