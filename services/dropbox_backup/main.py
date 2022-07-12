from dropbox_file_uploader import DropboxFileUploader

from generate_backup_zip import GenerateBackupZip


if __name__ == "__main__":
    dfu = DropboxFileUploader()
    gbz = GenerateBackupZip()
    
    mongo_backup_file = gbz.generate_mongodb_backup_zip()
    dfu.upload(mongo_backup_file)
    
    files_backup_file = gbz.generate_apk_backup_zip()
    # dfu.upload(files_backup_file)
    