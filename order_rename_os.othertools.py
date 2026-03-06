PATH_TO_SOURCE = "\\\\webdav.cloud.mail.ru@SSL\\DavWWWRoot\\Camera Uploads\\"
PATH_TO_ARCHIVE = "\\\\webdav.cloud.mail.ru@SSL\\DavWWWRoot\\Foto (Фото)\\" 
IMG_BEGIN = "IMG_"
VID_BEGIN = "VID_"
PANO_BEGIN = "PANO_"
SCRN_BEGIN = "Screenshot_"
SCRN_BEGIN_MP4 = "Screenrecorder-"
import os

def start_process(PATH_TO_ARCHIVE):
    print("List")
    for listitem in os.listdir(PATH_TO_SOURCE):
        if os.path.isfile(os.path.join(PATH_TO_SOURCE, listitem)):
            if listitem.startswith(IMG_BEGIN): listitem = listitem.replace(IMG_BEGIN, '')
            if listitem.startswith(VID_BEGIN): listitem = listitem.replace(VID_BEGIN, '')
            if listitem.startswith(PANO_BEGIN): listitem = listitem.replace(PANO_BEGIN, '')
            if listitem.startswith(SCRN_BEGIN): listitem = listitem.replace(SCRN_BEGIN, '')
            if listitem.startswith(SCRN_BEGIN_MP4): listitem = listitem.replace(SCRN_BEGIN_MP4, '')

            myyear = listitem[0:4]
            # print(myyear, ": ", listitem)
            

            # for putitem in os.listdir(PATH_TO_ARCHIVE):
            #     if os.path.exists(os.path.join(PATH_TO_ARCHIVE, myyear)):

    # for listitem in os.listdir(PATH_TO_ARCHIVE):
    #     print(listitem, end='')
    #     if os.path.isdir(os.path.join(PATH_TO_ARCHIVE, listitem)):
    #         print(", каталог")
    #     else:
    #         print(", файл")

if os.path.exists(PATH_TO_ARCHIVE):
    print("Указанный файл существует") 
    start_process(PATH_TO_ARCHIVE)
else:
    print("Файл не существует") 



def change_file():
    pass

