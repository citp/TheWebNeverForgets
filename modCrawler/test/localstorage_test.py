import unittest
import crawler.common as cm
import extractor.localstorage as ls
import crawler.ffmod as ffm
import sttest
import utils.db_utils as dbu
EXPECTED_LS_ORIGIN = 'https://.%s:443' % cm.ONLINE_TEST_HOST
EXPECTED_LS_KEY = 'testkey'
EXPECTED_LS_VALUE = 'Test-0123456789'
LS_TEST_URL = cm.BASE_TEST_URL + '/evercookie/localstorage.html'


class Test(sttest.STTest):

    def test_ls_item_by_visit(self):
        results = ffm.visit_page(LS_TEST_URL, wait_on_site=1)
        ls_items = results["local_storage"]
        self.assertEqual(len(ls_items), 1,
                         'There should only be one item in localstorage %d' %
                         len(ls_items))
        for ls_row in ls_items:
            scope, key, value = ls_row
            origin = ls.get_ls_origin_from_scope(scope)
            self.assertEqual(key, EXPECTED_LS_KEY)
            self.assertEqual(value, EXPECTED_LS_VALUE)
            self.assertEqual(origin, EXPECTED_LS_ORIGIN)
        self.check_localstorage_db_ops(ls_items)

    def test_get_ls_origin_from_scope(self):
        scope = 'eb.elgoog.www.:https:443'
        expected_origin = 'https://.www.google.be:443'
        origin = ls.get_ls_origin_from_scope(scope)
        self.assertEqual(origin, expected_origin)

    def check_localstorage_db_ops(self, ls_items):
        # dbu.insert_to_db(dbu.DBCmd.ADD_LOCALSTORAGE_ITEMS, ls_items, self.vi)
        ls_items_db = dbu.get_db_entry(self.vi.out_db,
                                       dbu.DBCmd.LOCALSTORAGE_BY_VISIT_ID,
                                       self.vi.visit_id).fetchall()
        self.assertEqual(len(ls_items_db), 1)
        for ls_row in ls_items_db:
            _, _, url, scope, key, value = ls_row
            self.assertEqual(scope, EXPECTED_LS_ORIGIN)
            self.assertEqual(key, EXPECTED_LS_KEY)
            self.assertEqual(value, EXPECTED_LS_VALUE)
            self.assertEqual(url, LS_TEST_URL)


if __name__ == "__main__":
    unittest.main()
