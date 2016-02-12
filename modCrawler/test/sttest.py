import unittest
import utils.gen_utils as ut
import utils.file_utils as fu
import utils.db_utils as dbu
import os
import crawler.common as cm


class STTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files_to_remove = []  # list of files to be removed during teardown

    @classmethod
    def tearDownClass(cls):
        for f in cls.files_to_remove:  # remove test files
            if os.path.lexists(f):
                fu.rm(f)

    def setUp(self):
        self.vi = cm.VisitInfo()
        self.vi.visit_id = 1
        self.test_db = os.path.join(cm.BASE_TMP_DIR, cm.DB_FILENAME)
        self.vi.out_db = self.test_db
        self.vi.out_dir = cm.BASE_TMP_DIR
        self.vi.err_log = os.path.join(cm.BASE_TMP_DIR, "err.log")
        self.vi.sys_log = os.path.join(cm.BASE_TMP_DIR, "sys.log")
        self.vi.ff_log = os.path.join(cm.BASE_TMP_DIR, "ff_test.log")
        self.vi.log_options = [cm.LOG_TO_FILE, cm.LOG_TO_CONSOLE]
        self.vi.url = "http://xyz.org"
        dbu.create_db_from_schema(self.test_db)
        self.files_to_remove.extend([self.test_db, self.vi.sys_log,
                                     self.vi.ff_log])

    def tearDown(self):
        fu.rm(self.test_db)

    def should_not_raise(self, msg, fn, *xargs, **kwargs):
        """Fail if the function does not raise."""
        try:
            fn(*xargs, **kwargs)
        except:
            self.fail(msg)
        else:
            pass

    def should_raise(self, msg, fn, *xargs, **kwargs):
        """Check if the function raises with given args."""
        try:
            fn(*xargs, **kwargs)
        except:
            pass
        else:
            self.fail(msg)

    def is_installed(self, pkg_name):
        """Check if a Linux package is installed."""
        cmd = 'which %s' % pkg_name
        status, _ = ut.run_cmd(cmd)
        return False if status else True

    def assert_is_installed(self, pkg):
        self.failUnless(self.is_installed(pkg),
                        'Cannot find %s in your system' % pkg)

    def assert_is_file(self, filename):
        """Check if the file exists."""
        self.assertTrue(os.path.isfile(filename),
                        "Cannot find file: %s" % filename)

    def assert_is_dir(self, dirname):
        """Check if the directory exists."""
        self.assertTrue(os.path.isdir(dirname),
                        "Cannot find directory: %s" % dirname)

    def assert_is_executable(self, binary):
        if not os.path.isfile(binary):
            self.fail('Cannot find %s' % binary)
        if not os.access(binary, os.X_OK):
            self.fail('Don\'t have execution permission for %s' % binary)

    def new_temp_file(self, filename):
        """Add file to remove-list."""
        self.files_to_remove.append(filename)
        return filename

    def assert_py_pkg_installed(self, pkg):
        if pkg == "pyOpenssl":
            pkg = "OpenSSL"
        elif pkg == "pypng":
            pkg = "png"
        elif pkg == "mitmproxy":
            pkg = "libmproxy"
        elif pkg == "Pillow":
            pkg = "Image"

        try:
            __import__(pkg)
        except ImportError:
            self.fail("Cannot find python package %s in your system" % pkg)
