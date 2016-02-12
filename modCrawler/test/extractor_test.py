import unittest
from time import strftime
import extractor.extractor as ex
import crawler.common as cm
import utils.db_utils as dbu
import sttest


class Test(sttest.STTest):

    def test_update_visit(self):
        test_url = "http://example.com"
        start_time = strftime("%Y%m%d-%H%M%S")
        be = cm.BrowserEvent()
        be.event_type = cm.EVENT_NEW_VISIT
        vi = cm.VisitInfo()
        vi.url = test_url
        vi.start_time = start_time
        vi.out_db = self.test_db
        vi.duration = 0
        vi.incomplete = 1

        vi.visit_id = dbu.insert_to_db(dbu.DBCmd.ADD_VISIT, be, vi)
        vi_read = dbu.get_db_entry(self.test_db, dbu.DBCmd.VISIT_BY_ID,
                                   vi.visit_id)
        self.assertEqual(vi.duration, vi_read.duration)
        self.assertEqual(vi.incomplete, vi_read.incomplete)

        vi.duration = 33
        vi.incomplete = 0
        dbu.insert_to_db(dbu.DBCmd.UPDATE_VISIT, be, vi)
        vi_read = dbu.get_db_entry(self.test_db, dbu.DBCmd.VISIT_BY_ID,
                                   vi.visit_id)
        self.assertEqual(vi.duration, vi_read.duration)
        self.assertEqual(vi.incomplete, vi_read.incomplete)

    def test_r_w_visit_to_db(self):
        test_url = "http://example.com"
        start_time = strftime("%Y%m%d-%H%M%S")
        be = cm.BrowserEvent()
        be.event_type = cm.EVENT_NEW_VISIT
        vi = cm.VisitInfo()
        vi.url = test_url
        vi.start_time = start_time
        vi.out_db = self.test_db
        visit_id = dbu.insert_to_db(dbu.DBCmd.ADD_VISIT, be, vi)
        vi_read = dbu.get_db_entry(self.test_db, dbu.DBCmd.VISIT_BY_ID,
                                   visit_id)
        self.assertEqual(vi.url, vi_read.url)
        self.assertEqual(vi.start_time, vi_read.start_time)

    def test_r_w_canvas_to_db(self):
        be = cm.BrowserEvent()
        be.event_type = cm.EVENT_TODATAURL
        be.url = "http://example.com"
        be.js_file = "http://example.com/fp.js"
        be.js_line = 5
        be.txt = "data:asdsads"
        vi = cm.VisitInfo()
        vi.visit_id = 1
        vi.out_db = self.test_db
        canvas_ev_id = dbu.insert_to_db(dbu.DBCmd.ADD_CANVAS, be, vi)
        self.assertGreater(canvas_ev_id, 0)
        visit_id, data_url_id, event_time, be_db = \
            dbu.get_db_entry(self.test_db, dbu.DBCmd.CANVAS_BY_ID,
                             canvas_ev_id)
        self.assertEqual(vi.visit_id, visit_id)
        self.assertEqual(data_url_id, 1)
        self.assertEqual(be_db.event_type, be.event_type)
        self.assertEqual(be_db.url, be.url)
        self.assertEqual(be_db.js_file, be.js_file)
        self.assertEqual(be_db.js_line, be.js_line)
        self.assertEqual(event_time, 0)

    def test_check_canvas_rw_access(self):
        common_url = "http://example.com/fp.js"
        be1 = cm.BrowserEvent()
        be1.event_type = cm.EVENT_TODATAURL
        be1.js_file = common_url

        be2 = cm.BrowserEvent()
        be2.event_type = cm.EVENT_FILLTEXT
        be2.js_file = common_url
        self.assertEqual([common_url],
                         ex.check_canvas_rw_access([be1, be2]))

    def test_check_canvas_rw_access_for_diff_js(self):
        url1 = "http://example.com/fp.js"
        url2 = "http://example.com/ga.js"

        be1 = cm.BrowserEvent()
        be1.event_type = cm.EVENT_TODATAURL
        be1.js_file = url1

        be2 = cm.BrowserEvent()
        be2.event_type = cm.EVENT_FILLTEXT
        be2.js_file = url2
        self.assertEqual([], ex.check_canvas_rw_access([be1, be2]))

if __name__ == "__main__":
    unittest.main()
