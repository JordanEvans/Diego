__author__ = 'dev'

import os

if __name__ == '__main__':

    path = '/home/dev/DiegoBackup'
    if not os.path.exists(path):
        os.mkdir(path)
    os.system("cp -purv *.py " + path)

    path = '/home/dev/DiegoGit'
    if not os.path.exists(path):
        os.mkdir(path)
    os.system("cp -purv *.py " + path)
    os.system("cp -puv '/home/dev/Diego/Stories/HanselAndGretel' /home/dev/DiegoGit/")
    os.system("cp -puv '/home/dev/Diego/Stories/Salem' /home/dev/DiegoGit/")
    os.system("cp -puv '/home/dev/Diego/README.md' /home/dev/DiegoGit/")
    os.system("cp -puv '/home/dev/Diego/widgetView.png' /home/dev/DiegoGit/")

    usbPath = '/media/dev/IUU/Diego/'
    os.system("cp -purv *.py " + usbPath)