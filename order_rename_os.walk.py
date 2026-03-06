PATH_TO_SOURCE = "\\\\webdav.cloud.mail.ru@SSL\\DavWWWRoot\\Camera Uploads\\"
PATH_TO_ARCHIVE = "\\\\webdav.cloud.mail.ru@SSL\\DavWWWRoot\\Foto (Фото)\\2024" 
IMG_BEGIN = "IMG_"
IMG_BEGIN = "VID_"

import os

def start_process(PATH_TO_ARCHIVE):
    for root, dirs, files in os.walk(PATH_TO_ARCHIVE):
        print('Корневой каталог: ' + root)

        for myfile in files:
            print('Файл в папке: ' + myfile)

            # print('Файл в папке  ' + root + '\\' + mydir + ': ' + myfile)
            # for mydir in dirs:
            #     print('Подпапка ' + root + '\\' + mydir)


            #change_file(root, name)

if os.path.exists(PATH_TO_ARCHIVE):
    print("Указанный файл существует") 
    start_process(PATH_TO_ARCHIVE)
else:
    print("Файл не существует") 



def change_file():
    pass

