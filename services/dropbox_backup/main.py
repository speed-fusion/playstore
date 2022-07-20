from dropbox_file_uploader import DropboxFileUploader

from generate_backup_zip import GenerateBackupZip


if __name__ == "__main__":
    dfu = DropboxFileUploader()
    gbz = GenerateBackupZip()
    
    gbz.generate_mongodb_backup_zip()
    # gbz.generate_apk_backup_zip()
    gbz.todays_zip.close()
    
    dfu.upload(gbz.zip_path)