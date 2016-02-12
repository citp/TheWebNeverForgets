import os
import unittest
import crawler.common as cm
import crawler.ffmod as ffm
import extractor.extractor as ex
import analysis.canvas as canvas
import sttest

join = os.path.join
CANVAS_BASE_TEST_URL = "%s/%s" % (cm.BASE_TEST_URL, "/canvas/")


class CanvasTest(sttest.STTest):

    def load_test_dataurl(self, filename):
        with open(os.path.join(cm.BASE_TEST_DATAURLS_DIR, filename), 'r') as f:
            return f.read()

    def test_img_dims(self):
        """Check whether we get sizes of a test image correctly."""
        dataurl = self.load_test_dataurl("favicon")
        expected_dims = (16, 16)
        dims = canvas.img_dims(dataurl)
        self.assertEqual(dims, expected_dims,
                         "Image dimensions: {0} don't match"
                         " expected dimensions: {1}."
                         .format(dims, expected_dims))

    def test_count_distinct_colors(self):
        """Check whether we get the right number of distinct colors."""
        dataurl = self.load_test_dataurl("solid_color")
        expected_colors = 1
        num_colors = canvas.count_distinct_colors(dataurl)
        self.assertEqual(num_colors, expected_colors,
                         "Number of colors: %s does not match "
                         "expected number of colors: %s"
                         % (num_colors, expected_colors))
        dataurl = self.load_test_dataurl("two_colors_alpha")
        expected_colors = 600
        num_colors = canvas.count_distinct_colors(dataurl)
        self.assertEqual(num_colors, expected_colors,
                         "Number of colors: %s does not match "
                         "expected number of colors: %s"
                         % (num_colors, expected_colors))
        dataurl = self.load_test_dataurl("canvas_fp")
        expected_colors = 2823
        num_colors = canvas.count_distinct_colors(dataurl)
        self.assertEqual(num_colors, expected_colors,
                         "Number of colors: %s does not match with "
                         "expected number of colors: %s"
                         % (num_colors, expected_colors))

    def test_decode_exception(self):
        test_text_not_b64 = "dataurl,not base64 text"
        pngdata = canvas.decode(test_text_not_b64, silence=True)
        self.assertIsNone(pngdata,
                          "base64 decode didn't return None for faulty data")

    def test_fill_text_calls(self):
        """ffmod should log the text that is written to the canvas."""
        ft_url = CANVAS_BASE_TEST_URL + "filltext.html"
        results = ffm.visit_page(ft_url, wait_on_site=1)
        calls = results["calls"]
        self.assertEqual(len(calls), 1, "Unexpected no of calls in logs: %d"
                         % len(calls))
        call = calls[0]
        self.assertEqual(call.initiator, 'CanvasRenderingContext2D.cpp',
                         "Unexpected FF source file name in the logs")
        self.assertEqual(call.event_type, 'FillText',
                         "Unexpected event name in the logs")
        self.assertTrue(call.js_file.endswith("filltext.html"),
                        "Unexpected JS source file name")
        self.assertEqual(call.js_line, '10',
                         "Unexpected JS line number in the logs")
        self.assertEqual(call.log_text, 'TEST-1234567890',
                         "Unexpected canvas fill text")

    def test_fill_text_to_dataurl_detection(self):
        ft_url = CANVAS_BASE_TEST_URL + "filltext_todataurl.html"
        results = ffm.visit_page(ft_url, wait_on_site=1)
        calls = results["calls"]
        if not ex.check_canvas_rw_access(calls):
            self.fail("Cannot find read/write access logs to canvas")

    def test_stroke_text_to_dataurl_detection(self):
        ft_url = CANVAS_BASE_TEST_URL + "stroketext_todataurl.html"
        results = ffm.visit_page(ft_url, wait_on_site=1)
        calls = results["calls"]
        if not ex.check_canvas_rw_access(calls):
            self.fail("Cannot find read/write access logs to canvas")

    def test_check_canvas_rw_access(self):
        ft_url = CANVAS_BASE_TEST_URL + "filltext.html"
        results = ffm.visit_page(ft_url, wait_on_site=1)
        calls = results["calls"]
        if ex.check_canvas_rw_access(calls):
            self.fail("Should not find read/write access logs to canvas")

    # ffmod should log extracted img data
    def test_to_data_url_br_test(self):
        ft_url = CANVAS_BASE_TEST_URL + "todataurl.html"
        results = ffm.visit_page(ft_url, wait_on_site=1)
        calls = results["calls"]
        self.assertEqual(len(calls), 2, "Unexpected no of calls in logs: %d"
                         % len(calls))
        call = calls[1]
        self.assertEqual(call.initiator, 'HTMLCanvasElement.cpp',
                         "Unexpected FF source file name in the logs")
        self.assertEqual(call.event_type, 'ToDataURL',
                         "Unexpected event name in the logs: %s"
                         % call.event_type)
        self.assertTrue(call.js_file.endswith("todataurl.html"),
                        "Unexpected JS source file name %s" % call.js_file)
        self.assertEqual(call.js_line, '17',
                         "Unexpected JS line number in the logs %s"
                         % call.js_line)
        self.assertEqual(call.log_text,
                         'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAA'
                         'BkCAYAAABw4pVUAAABHElEQVR4nO3RwW3DQAADwSvWhaS7uCvnz2'
                         'cgYKVkBmAD3HMAAACAB3qf8/mrq7/9lfo0QUZ9miCjPk2QUZ8myK'
                         'hPE2TUpwky6tMEGfVpgoz6NEFGfZogoz5NkFGfJsioTxNk1KcJMu'
                         'rTBBn1aYKM+jRBRn2aIKM+TZBx9Qmv87rNzvn+unaCCCKIIIIIIo'
                         'gggggiiCCCCCKIIIIIIogggggiiCCCCCKIIIIIIogggggiiCCCCH'
                         'KDEIIIIoggggjyL4Nc7+oT7rRHqk8TZNSnCTLq0wQZ9WmCjPo0QU'
                         'Z9miCjPk2QUZ8myKhPE2TUpwky6tMEGfVpgoz6NEFGfZogoz5NkF'
                         'GfJsioTxNk1KcJMurTBAEAAAAAAACAJ/kBNTWUxDGSNrkAAAAASU'
                         'VORK5CYII=',
                         "Unexpected canvas data URL %s" % call.log_text)


if __name__ == "__main__":
    unittest.main()
