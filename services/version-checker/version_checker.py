from datetime import datetime
from database import Database
from helper import generate_file_id
from apkpure_scraper import ApkpureScraper
import os

class VersionChecker:
    def __init__(self) -> None:
        
        self.db = Database()
        self.scraper = ApkpureScraper()
    
    
    def main(self):
        
        apps = list(self.db.application.find({"status":"scraping","error_count":{"$lt":10}}))
        
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
            
            filename,file_id = generate_file_id(package_name,version,version_code,published_on)
            
            data["_id"] = file_id
            data["filename"] = filename
            data["package_id"] = package_id
            data["version_unique_id"] = file_id
            data["error_count"] = 0
            
            self.db.add_file(data)
            
            self.db.update_application(package_id,{"status":"active"})
            
            t2 = datetime.now()
            
            print(f'total seconds : {(t2 - t1).seconds}')
        os.exit(0)
        
if __name__ == "__main__":
    vc = VersionChecker()
    vc.main()