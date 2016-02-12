import unittest
import crawler.common as cm
import utils.web_utils as wu
import utils.census_utils as cu
import sttest


class WebUtilsTest(sttest.STTest):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_url(self):
        page_html = wu.read_url('http://www.google.com')
        self.assertIn('<html', page_html, "Cannot find html tag")

    def assert_public_suffix(self, url, expected_pub_suffix):
        self.assertEqual(cu.get_tld(url),
                         expected_pub_suffix,
                         'Unexpected public suffix (%s) for URL %s' %
                         (expected_pub_suffix, url))

    def test_get_extract_domain(self):
        urls = ('http://www.foo.org',
                'https://www.foo.org',
                'http://www.subdomain.foo.org',
                'http://www.subdomain.foo.org:80/subfolder',
                'https://www.sub.foo.org:80/subfolder?param1=4&param2=5',
                'https://www.sub.foo.org:80/subfolder/bae654sadfasd==/654fasd')
        for pub_suf_test_url in urls:
            self.assert_public_suffix(pub_suf_test_url, 'foo.org')

    def test_gen_url_list(self):
        self.assert_is_file(cm.ALEXA_TOP_1M)
        self.assertEqual(list(wu.gen_url_list(0)), [])
        self.assertEqual(len(list(wu.gen_url_list(10))), 10,
                         "Unexpected no of URLs")

    def test_get_top_alexa_list_start_stop(self):
        top_50_100 = list(wu.gen_url_list(100, 50))
        self.assertEqual(len(top_50_100), 51)

        top_5_10 = list(wu.gen_url_list(10, 5))
        self.assertEqual(len(top_5_10), 6)


if __name__ == "__main__":
    unittest.main()
