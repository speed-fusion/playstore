import os
import dropbox
from datetime import datetime
from pathlib import Path

class DropboxFileUploader:
    def __init__(self) -> None:
        # self.access_token = os.environ.get("DROPBOX_ACCESS_TOKEN")
        self.access_token = "sl.BLTuM5UECYevS03-7HmXXF5O0FE4yuaGxeY6fNccZEMrREM9jpFCpbx1nexnfGd7-I78upzV-7ogHX0x2eeZ-lNRMBFxNZqOM-nw2QyBaADQG_1G_MvyPoUHsyQmWsoJwmJj68w"
        self.dropbox = dropbox.Dropbox(self.access_token)
        self.now = datetime.now()
        self.upload_dir = f'/cdn.onehost.io/'
    
    def upload(self,file_path:Path):
        with open(file_path,"rb") as f:
            self.dropbox.files_upload(f.read(),self.upload_dir + file_path.name)


if __name__ == "__main__":
    db = DropboxFileUploader()
    db.upload(Path("test.txt"))
    print(db.dropbox.files_list_folder())