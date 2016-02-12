import unittest
import analysis.extract_evercookies as ev


class Test(unittest.TestCase):

    def test_has_json(self):
        swf_jsons = ("{'timeStamp':355000, 'GUID': 979, 'isPlayingNow': True}",
                     "{'key_SUV': u'1404290345336071'}",
                     "ext_key: {'key_SUV': u'1404296071'}",  # string + JSON
                     )
        non_jsons = ("{''a':3}", "{'a'3}", "{'a'}", "{'a':}",)
        for swf_json in swf_jsons:
            self.assertTrue(ev.has_json(swf_json), "%s" % swf_json)
        for swf_json in non_jsons:
            self.assertFalse(ev.has_json(swf_json), "%s" % swf_json)

    def test_is_base64_encoded(self):
        s = "a"
        self.assertEqual(s, ev.decode_if_b64(s))

    def test_split_lso(self):
        print ev.split_lso("abc:123;444_guid=4654645")
        print ev.split_lso("GrNeUzbEibiiqqoEht1MCwEAAAA=")
        print ev.split_lso("machine_cookie=ea41f86361cfe31193ff6eae8b286ba1")

if __name__ == "__main__":
    unittest.main()
