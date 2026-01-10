import shutil
import os


def backup_file(file_path: str):
    backup_path = file_path + ".bak"
    shutil.copy(file_path, backup_path)


def restore_backup(file_path: str):
    backup_path = file_path + ".bak"
    if os.path.exists(backup_path):
        shutil.copy(backup_path, file_path)
