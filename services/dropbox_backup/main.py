from dropbox_file_uploader import DropboxFileUploader

from generate_backup_zip import GenerateBackupZip


if __name__ == "__main__":
    dfu = DropboxFileUploader()
    gbz = GenerateBackupZip()
    
    # generate mongo backup and add generated files in zip
    # gbz.generate_mongodb_backup_zip()
    
    # add apk files into backup.
    # gbz.generate_apk_backup_zip()
    
    # close the file before uploading
    # gbz.todays_zip.close()
    
    # upload generated zip in dropbox
    dfu.upload(gbz.zip_path)
    
    # manage backup files
    dfu.manage_backup_files()
    
    # delete the zip file after uploaded to dropbox
    gbz.zip_path.unlink()