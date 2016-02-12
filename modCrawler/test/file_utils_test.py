import os
import unittest
import inspect
import utils.file_utils as fu
import utils.gen_utils as ut
import sttest
REGEXP_FILES_DIR = os.path.join("files", "fileutils")


class Test(sttest.STTest):

    def test_write_to_file(self):
        filename = self.new_temp_file('write_test.txt')
        random_str = ut.rand_str(100)
        fu.write_to_file(filename, random_str)
        self.assertEqual(random_str, fu.read_file(filename))

    def test_read_file(self):
        file_content = fu.read_file(os.path.realpath(__file__))
        if 'whatever written here' not in file_content:
            self.fail('Cannot read itself')

    def test_add_symlink(self):
        test_link = self.new_temp_file('test_link')
        src_file = self.new_temp_file('linktest.txt')
        fu.write_to_file(src_file, "link test")
        fu.add_symlink(test_link, src_file)
        self.failUnless(os.path.lexists(test_link))

    def test_gen_find_files(self):
        # Should match files in subdirectories
        results = set(fu.gen_find_files('regexp*.txt', REGEXP_FILES_DIR))
        regex_files = set(('%s/regexp2.txt' % REGEXP_FILES_DIR,
                           '%s/regexp.txt' % REGEXP_FILES_DIR,
                           '%s/sub/regexp.txt' % REGEXP_FILES_DIR))
        self.assertSetEqual(results, regex_files)

    def test_gen_cat_file(self):
        result = fu.gen_cat_file(os.path.join(REGEXP_FILES_DIR,
                                              'regexp.txt'))
        self.failUnless(inspect.isgenerator(result))
        self.assertEqual(6, len(list(result)))

    def test_get_basename_from_url(self):
        url = 'http://example.com'
        prefix = '2'
        self.assertEqual(fu.get_basename_from_url(url, prefix),
                         '%s-http-example-com' % (prefix))
        url = 'example.com/'
        prefix = '2'
        self.assertEqual(fu.get_basename_from_url(url, prefix),
                         '%s-example-com-' % (prefix))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_init_db']
    unittest.main()
