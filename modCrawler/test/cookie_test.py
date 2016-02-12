import unittest
import sttest
import crawler.common as cm
import crawler.ffmod as ffm

TEST_COOKIE_ORIGIN = cm.ONLINE_TEST_DOMAIN
TEST_COOKIE_HOST = cm.ONLINE_TEST_HOST
TEST_COOKIE_NAME = "test_cookie"
TEST_COOKIE_VALUE = "Test-0123456789"
COOKIE_TEST_URL = cm.BASE_TEST_URL + '/evercookie/cookie.html'
THIRD_PARTY_COOKIE_TEST_URL = "http://jsbin.com/daqayuti/1"
# Source code for the above jsbin can be found in the repo:
# test/files/online_tests/evercookie/jsbin_3rdP_cookie_test.html


class Test(sttest.STTest):

    def test_3rdparty_cookie_set(self):
        cookie_names = []
        cookie_origins = []
        results = ffm.visit_page(THIRD_PARTY_COOKIE_TEST_URL,
                                 wait_on_site=5)
        cookies = results["cookies"]
        # print cookies
        for cookie in cookies:
            cookie_names.append(cookie[1])
            cookie_origins.append(cookie[0])
        self.assertIn(TEST_COOKIE_NAME, cookie_names)
        self.assertIn(TEST_COOKIE_ORIGIN, cookie_origins)

    def test_disable_3rdp_cookies(self):
        third_p_origin = TEST_COOKIE_ORIGIN
        results = ffm.visit_page(THIRD_PARTY_COOKIE_TEST_URL,
                                 wait_on_site=5,
                                 cookie_support=cm.COOKIE_ALLOW_1ST_PARTY)
        cookies = results["cookies"]
        for cookie in cookies:
            origin = cookie[0]
            self.assertNotEqual(origin, third_p_origin,
                                "Should not accept 3rd party cookies")

    def test_js_cookies_by_visit_ff(self):
        results = ffm.visit_page(COOKIE_TEST_URL, wait_on_site=3)
        cookies = results["cookies"]
        self.assertEqual(len(cookies), 1)
        cookie = cookies[0]
        origin, name, value, host = cookie[0:4]
        self.assertEqual(origin, TEST_COOKIE_ORIGIN)
        self.assertEqual(name, TEST_COOKIE_NAME)
        self.assertEqual(value, TEST_COOKIE_VALUE)
        self.assertEqual(host, TEST_COOKIE_HOST)

    def test_disable_cookies(self):
        results = ffm.visit_page(COOKIE_TEST_URL, wait_on_site=3,
                                 cookie_support=cm.COOKIE_ALLOW_NONE)
        cookies = results["cookies"]
        self.assertEqual(len(cookies), 0)


if __name__ == "__main__":
    unittest.main()
