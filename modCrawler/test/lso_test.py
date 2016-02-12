import unittest
import os
import crawler.common as cm
import crawler.ffmod as ffm
from utils.gen_utils import rand_str
import extractor.lso as lso
import utils.db_utils as dbu
import sttest

TEST_LSO_FILENAME = "FlashCookie.sol"
TEST_LSO_REL_PATH = os.path.join("2NFXEHPV", "example.com", TEST_LSO_FILENAME)
TEST_LSO_KEYNAME = "test_key"
TEST_LSO_VALUE = "6fn6vc"


class Test(sttest.STTest):
    def setUp(self):
        sttest.STTest.setUp(self)
        self.vi.sys_log = os.path.join(cm.BASE_TEST_FILES_DIR, "evercookie",
                                       "test_syscall.log")
        self.lso_file = os.path.join(cm.BASE_TEST_FILES_DIR, "evercookie",
                                     "#SharedObjects", TEST_LSO_REL_PATH)

    def test_parse_strace_logs(self):
        lso_events = lso.parse_strace_logs(self.vi, test_lso=self.lso_file)
        self.assertEqual(len(lso_events), 1)
        lso_event = lso_events[0]
        self.assertEqual(lso_event.js_line, "")
        self.assertEqual(lso_event.log_text,
                         TEST_LSO_VALUE)
        self.assertEqual(lso_event.initiator, cm.ONLINE_TEST_HOST)
        self.assertEqual(lso_event.js_file, TEST_LSO_FILENAME)
        self.assertEqual(lso_event.cookie_path, TEST_LSO_REL_PATH)

    def test_lso_db_ops(self):
        lso_events = lso.parse_strace_logs(self.vi, test_lso=self.lso_file)
        dbu.insert_to_db(dbu.DBCmd.ADD_LSO_ITEMS, lso_events, self.vi)
        lso_items_db = dbu.get_db_entry(self.vi.out_db,
                                        dbu.DBCmd.GET_FLASH_COOKIES,
                                        self.vi.visit_id).fetchall()
        self.assertEqual(len(lso_items_db), 1)
        lso_event = lso_items_db[0]
        page_url, domain, filename, local_path, key, content = lso_event[2:8]
        self.assertEqual(page_url, self.vi.url)
        self.assertEqual(domain, cm.ONLINE_TEST_HOST)
        self.assertEqual(filename, TEST_LSO_FILENAME)
        self.assertEqual(local_path, TEST_LSO_REL_PATH)
        self.assertEqual(key, TEST_LSO_KEYNAME)
        self.assertEqual(content, TEST_LSO_VALUE)

    def test_get_lso_from_visit(self):
        lso_found = False
        lso_value = rand_str()
        qry_str = '?lso_test_key=%s&lso_test_value=%s' % ("test_key",
                                                          lso_value)
        test_url = cm.BASE_TEST_URL + '/evercookie/lso/setlso.html' + qry_str
        results = ffm.visit_page(test_url, wait_on_site=3)
        lso_items = results["flash_cookies"]
        self.failUnless(len(lso_items))

        for test_lso in lso_items:
            self.assertEqual(test_lso.event_type, cm.EVENT_FLASH_LSO)
            self.assertIn(cm.ONLINE_TEST_HOST, test_lso.initiator)
            if TEST_LSO_KEYNAME == test_lso.key:
                self.assertEqual(lso_value, test_lso.log_text)
                lso_found = True
        self.failUnless(lso_found, "Cannot find LSO with the value %s in %s" %
                        (lso_value, lso_items))

    def test_disable_flash(self):
        lso_value = rand_str()
        qry_str = '?lso_test_key=%s&lso_test_value=%s' % ("test_key",
                                                          lso_value)
        test_url = cm.BASE_TEST_URL + '/evercookie/lso/setlso.html' + qry_str
        results = ffm.visit_page(test_url, wait_on_site=3,
                                 flash_support=cm.FLASH_DISABLE)
        lso_items = results["flash_cookies"]
        self.assertEqual(len(lso_items), 0)

if __name__ == "__main__":
    unittest.main()
