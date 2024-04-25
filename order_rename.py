BEGIN_OF_PATHES = "\\\\webdav.cloud.mail.ru@SSL\\DavWWWRoot"
# "D:\\study\Python\\cloud.mail.ru - порядок в фотоальбомах"   
PATH_TO_SOURCE = BEGIN_OF_PATHES + "\\Camera Uploads\\"
PATH_TO_ARCHIVE = BEGIN_OF_PATHES + "\\Foto (Фото)\\" 

FILE_NAME_BEGIN_LIST = ["IMG_", "VID_", "PANO_", "Screenshot_", "Screenrecorder-"]

import os
from pathlib import Path

archive_folder = Path(PATH_TO_ARCHIVE)                      #(PATH_TO_SOURCE)
data_folder = Path(PATH_TO_SOURCE)                          #(PATH_TO_SOURCE)
data_folder_files = data_folder.glob("*.*")
# global filecount = len(os.listdir(data_folder))

def start_process():
    for myfile in sorted(data_folder_files):
        # print(f"Файл: {myfile}")cl
        firstfilename = myfile.name   
        filename = myfile.name   
        for beginitem in FILE_NAME_BEGIN_LIST:
            if beginitem in filename:
                #print(f"{begitnitem} начинает имя файла {filename}")
                filename = str.replace(filename, beginitem, "")
        filename = str.replace(filename, "-", "")
        
        files_archive_folder = Path(f"{archive_folder}/{filename[0:4]}/{filename[4:6]}.{filename[6:8]}")
        files_archive_folder.mkdir(parents=True, exist_ok=True)
        target_path = files_archive_folder/firstfilename
        _ = myfile.rename(target_path)
        # global filecount = filecount - 1
        # print(filecount)
        # # clear = lambda: os.system('cls')
        # clear()

if os.path.exists(PATH_TO_SOURCE):
    print("Указанный каталог существует") 
    start_process()
else:
    print("Файл не существует")



def change_file():
    pass

