import unittest
import utils.gen_utils as ut
from time import sleep, time


class UtilsTest(unittest.TestCase):

    def test_cancel_timeout(self):
        start_time = time()
        ut.timeout(1)
        sleep(0.3)
        ut.cancel_timeout()
        elapsed_time = time() - start_time
        self.assertLess(elapsed_time, 5, 'Cannot cancel timer: %s' %
                        elapsed_time)

    def test_rand_str(self):
        # Test default parameters
        random_str = ut.rand_str()
        self.assertEqual(ut.DEFAULT_RAND_STR_SIZE, len(random_str),
                         "rand_str does not return string with default size!")
        self.failIf(set(random_str) - set(ut.DEFAULT_RAND_STR_CHARS),
                    "Unexpected characters in string!")

        # Test with different sizes and charsets
        sizes = [1, 2, 10, 100]
        charsets = (ut.DEFAULT_RAND_STR_CHARS, ut.DIGITS)
        for size in sizes:
            for charset in charsets:
                random_str = ut.rand_str(size, charset)
                self.assertEqual(len(random_str), size,
                                 "Unexpected random string size!")
                self.failIf(set(random_str) - set(ut.DEFAULT_RAND_STR_CHARS),
                            "Unexpected characters in string!")

if __name__ == "__main__":
    unittest.main()
