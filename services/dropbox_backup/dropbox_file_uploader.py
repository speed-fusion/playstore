import os
import dropbox
from datetime import datetime
from pathlib import Path

class DropboxFileUploader:
    def __init__(self) -> None:
        self.access_token = os.environ.get("DROPBOX_ACCESS_TOKEN")
        self.dropbox = dropbox.Dropbox(self.access_token)
        self.now = datetime.now()
        self.upload_dir = f'/app_manager_backup/{self.now.year}/{self.now.month}/'
    
    def upload(self,file_path:Path):
        with open(file_path,"rb") as f:
            self.dropbox.files_upload(f.read(),self.upload_dir + file_path.name)


if __name__ == "__main__":
    db = DropboxFileUploader()
    db.upload("test.txt")