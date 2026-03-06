# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os

DIRECTORY = r"D:\PythonProjects\Course\RenameFiles\Test"


def rename_files(find_directory):
    for root, dirs, files in os.walk(find_directory):
        for name in files:
            rename_file(root, name)


def rename_file(root, name):
    valid_name = get_valid_name(name)
    old_file = os.path.join(root, name)
    new_file = os.path.join(root, valid_name)
    os.rename(old_file, new_file)


def get_valid_name(name):
    name = name.replace("_Diff.", "_BC.")
    name = name.replace("_Diffuse.", "_BC.")
    name = name.replace("_Normal.", "_N.")
    name = name.replace("_ORM.", "_AORM.")
    name = name.replace("_O.", "_A.")
    if not name.startswith("T_"):
        name = "T_" + name
    return name


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    rename_files(DIRECTORY)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
