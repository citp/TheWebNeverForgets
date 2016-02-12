import os
import unittest
import sttest
import crawler.mitm as mitm
import crawler.ffmod as ffm
join = os.path.join


class Test(sttest.STTest):

    def test_get_free_port(self):
        self.assertTrue(mitm.get_free_port(),
                        "Cannot get a free port")

    def test_mitm_interception(self):
        found_http_req = False
        req_url = "http://example.com"
        results = ffm.visit_page(req_url,
                                 wait_on_site=1,
                                 out_dir=self.vi.out_dir)
        http_msgs = results["http_msgs"]
        self.assertTrue(len(http_msgs))
        for http_msg in http_msgs:
            # print http_msg["req_url"]
            self.assertTrue(len(http_msg["req_url"]))
            self.assertTrue(len(http_msg["req_headers"]))
            if req_url in http_msg["req_url"]:
                found_http_req = True
        self.assertTrue(found_http_req, "Cannot intercept HTTP requests")

    def test_ssl_mitm_interception(self):
        found_https_req = False
        req_url = "https://twitter.com/"
        results = ffm.visit_page(req_url,
                                 wait_on_site=1,
                                 out_dir=self.vi.out_dir)
        http_msgs = results["http_msgs"]
        self.assertTrue(len(http_msgs))
        for http_msg in http_msgs:
            print http_msg["req_url"]
            self.assertTrue(len(http_msg["req_url"]))
            self.assertTrue(len(http_msg["req_headers"]))
            if req_url in http_msg["req_url"]:
                found_https_req = True
        self.assertTrue(found_https_req, "Cannot intercept HTTPS requests")


if __name__ == "__main__":
    unittest.main()
