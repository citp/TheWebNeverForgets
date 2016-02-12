import re
import os
import fnmatch
from time import strftime


def rm(path):
    """Remove a file if it exist."""
    if os.path.isfile(path) or os.path.islink(path):
        os.unlink(path)


def create_dir(dir_path):
    """Create a dir if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def append_timestamp(_str):
    """Append a timestamp and return it."""
    return _str + strftime('%y%m%d_%H%M%S')


def read_file(path):
    """Read and return file content."""
    with open(path, 'rU') as f:
        content = f.read()
        f.close()
        return content


def write_to_file(file_path, data):
    """Write data to file and close."""
    f = open(file_path, 'w')
    f.write(data)
    f.close()


def append_to_file(file_path, data):
    """Write data to file and close."""
    with open(file_path, 'a') as ofile:
        ofile.write(data)


def add_symlink(linkname, src_file):
    """Create a symbolic link pointing to src_file"""
    if os.path.lexists(linkname):   # check and remove if link exists
        try:
            os.unlink(linkname)
        except:
            pass
    try:
        os.symlink(src_file, linkname)
    except:
        pass


def gen_find_files(filepat, top):
    """Returns filenames that matches the given pattern under() a given dir
    http://www.dabeaz.com/generators/
    """
    for path, _, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, filepat):
            yield os.path.join(path, name)


def gen_cat_file(filename):
    """Yield lines in a file."""
    f = open(filename, 'rU')
    for line in f:
        yield line


def get_basename_from_url(url, prefix):
    """Return base filename for the url."""
    dashed = re.sub(r'[\W]', '-', url)
    return prefix + '-' + re.sub(r'-+', '-', dashed)
