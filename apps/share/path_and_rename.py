import os

from django.utils.crypto import get_random_string


def path_and_rename(path, filename):
    file_root, file_ext = os.path.splitext(filename)
    filename = '{}{}'.format(get_random_string(20).lower(), file_ext)

    return os.path.join(path, filename)