from datetime import datetime

import pymongo
from database import Database
from helper import generate_file_id,generate_filename
from apkpure_scraper import ApkpureScraper
import os
import time
from pathlib import Path
class VersionChecker:
    def __init__(self) -> None:
        
        self.db = Database()
        self.scraper = ApkpureScraper()
        self.downloads = Path("/downloads")
    
    
    def main(self):
        
        apps = list(self.db.application.find({"status":"active","error_count":{"$lt":10}}))
        
        for app in apps:
            print(f'processing -> {app["_id"]}')
            t1 = datetime.now()
            package_url = app["package_url"]
            package_id = app["_id"]
            
            status,data = self.scraper.scrape_app_details(package_url)
            
            if status == False:
                self.db.update_application(package_id,{"error_count":app["error_count"] + 1})
                continue
            
            data["status"] = "scraped"
            
            package_name = app["package_name"]
            version = data["version"]
            version_code = data["version_code"]
            published_on = data["published_on_text"]
            
            _,file_id = generate_file_id(package_name,version,version_code,published_on)
            filename = generate_filename(package_name,version)
            data["_id"] = file_id
            data["filename"] = filename
            data["package_id"] = package_id
            data["version_unique_id"] = file_id
            data["error_count"] = 0
            
            self.db.add_file(data)
            
            self.db.update_application(package_id,{"status":"active"})
            
            t2 = datetime.now()
            
            print(f'total seconds : {(t2 - t1).seconds}')
    
    def version_manager(self):
        
        all_apps = list(self.db.application.find({"status":"active"}))
        
        for app in all_apps:
            versions = list(self.db.files.find({"package_id":app["_id"],"status":"active"}).sort("published_on_timestamp",pymongo.DESCENDING))
            
            for v in versions[4:]:
                
                folder_path = self.downloads.joinpath(app["_id"])
                
                file_path = folder_path.joinpath(v["filename"] + ".apk")
                
                if file_path.exists():
                    file_path.unlink()
                
                self.db.files.delete_one({"_id":v["_id"]})
                
                print(f'version deleted : {v}')
                
if __name__ == "__main__":
    sleep_time = 1 * 60 * 60
    while True:
        vc = VersionChecker()
        vc.main()
        time.sleep(30 * 60)
        vc.version_manager()
        time.sleep(30 * 60)
