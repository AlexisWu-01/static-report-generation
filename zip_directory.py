import shutil
import sys

def zip_directory(dirName):
    """
    Creates a compressed copy of the given directory.

    :param dirName: (str) the name of the directory to zip
    :returns: none, makes a zipped directory file
    """
    shutil.make_archive(dirName, 'zip', dirName)


if __name__ == '__main__':
    # get year and month from sys args
    year, month = sys.argv[1], sys.argv[2]

    zip_directory(f'{year}-{month}')
