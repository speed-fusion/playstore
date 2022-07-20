import pickle
import os
import dropbox
from datetime import datetime
from pathlib import Path
from dropbox import DropboxOAuth2FlowNoRedirect

class DropboxFileUploader:
    def __init__(self) -> None:
        self.token_manager = DropboxOfflineTokenManager()
        self.access_token = self.token_manager.get_token()
        self.dropbox = dropbox.Dropbox(oauth2_refresh_token=self.access_token,app_key=self.token_manager.APP_KEY)
        self.now = datetime.now()
        self.upload_dir = f'/cdn.onehost.io'
        self.max_backup_file_count = 19
    
    def upload(self,file_path:Path):
        with open(file_path,"rb") as f:
            self.dropbox.files_upload(f.read(),self.upload_dir + "/" + file_path.name)
    
    def manage_backup_files(self):
        files = self.dropbox.files_list_folder(self.upload_dir, limit=30).entries
        sorted_files = sorted(files, key=lambda entry: entry.server_modified,reverse=True)
        
        for i in sorted_files[self.max_backup_file_count:]:
            self.dropbox.files_delete(i.path_display)
            print(f'deleted : {i.name}')


class DropboxOfflineTokenManager:
    def __init__(self) -> None:
        self.APP_KEY = "xokf3h1wu1wh4bt"
        self.use_pkce = True
        self.token_type = "offline"
        self.refresh_token = None
        self.cwd = Path.cwd()
        self.refresh_token_file = self.cwd.joinpath("refresh_token.h5")
    
    def get_token(self):
        if self.refresh_token != None:
            return self.refresh_token
        
        if self.refresh_token_file.exists() == True:
            return self.load_refresh_token_from_file()
        
        auth_flow = DropboxOAuth2FlowNoRedirect(self.APP_KEY,use_pkce=self.use_pkce, token_access_type=self.token_type)
        
        url = auth_flow.start()
        
        print(f'url -> {url}')
        
        auth_code = input("Enter the code :")
        
        oauth_result = auth_flow.finish(auth_code)
        
        refresh_token = oauth_result.refresh_token
        
        self.refresh_token = refresh_token
        
        self.save_refresh_token_in_file()
        
        return self.refresh_token
        
        
    def load_refresh_token_from_file(self):
        with open(self.refresh_token_file,"rb") as f:
            data = pickle.load(f)
            self.refresh_token = data["refresh_token"]
            return self.refresh_token
        
    def save_refresh_token_in_file(self): 
        with open(self.refresh_token_file,"wb") as f:
            pickle.dump({"refresh_token":self.refresh_token},f)
        return self.refresh_token
    
    def get_user_info(self):
        with dropbox.Dropbox(oauth2_refresh_token=self.refresh_token, app_key=self.APP_KEY) as dbx:
            user_info = dbx.users_get_current_account()
            account_id = user_info.account_id
            email = user_info.email
            print("---------------------------------------------------------------------")
            print(f'account id : {account_id}')
            print(f'email : {email}')
            print(f'logged in...')
            print("---------------------------------------------------------------------")


if __name__ == "__main__":
    dboff = DropboxFileUploader()
    dboff.manage_backup_files()