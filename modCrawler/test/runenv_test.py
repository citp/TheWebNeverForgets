import os
import unittest
import sttest
import crawler.common as cm

# To run from cmd line, run the following from the base dir (test/..)
# python -m test.runenv_test


class RunEnvTest(sttest.STTest):
    def test_mitmdump_pkg(self):
        self.assert_is_installed('mitmdump')

    def test_py_pkgs(self):
        for pkg in open(cm.PY_REQUIREMENTS_FILE).readlines():
            pkg = pkg.strip().replace(">", " ").\
                replace("=", " ").replace("<", " ").split()[0]
            print "Checking Python package", pkg
            self.assert_py_pkg_installed(pkg)

    def test_run_dirs(self):
        run_dirs = (cm.BASE_JOBS_DIR,
                    cm.BASE_BIN_DIR,
                    cm.BASE_TMP_DIR)
        for run_dir in run_dirs:
            self.failUnless(os.path.isdir(run_dir),
                            'Cannot find dir: %s' % run_dir)

    def test_ff_mod_bin(self):
        self.assert_is_file(os.path.join(cm.BASE_BIN_DIR, "ff-mod", "firefox"))

    def test_alexa_list(self):
        self.assert_is_file(cm.ALEXA_TOP_1M)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_init_db']
    unittest.main()
