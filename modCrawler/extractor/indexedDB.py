import os
import utils.file_utils as fu
import sqlite3
import shutil


def gen_ff_indexedDB(visit_info):
    """Return indexeddb content from a FF profile folder.

    This function is experimental. The content may not be decoded
    properly. You can use "strings" command to manually dump the
    printable strings from a IndexedDB database.
    """

    prof_dir = os.path.expanduser(visit_info.profile_dir)
    for idb_file in fu.gen_find_files("*.sqlite", prof_dir):
        if ('storage/persistent' in idb_file or 'storage/permanent' in idb_file) and \
                'ent/chrome' not in idb_file and \
                "ent/moz-safe" not in idb_file:  # FF's own db.
                # "ent/" matches permanent and persistent
            # print_log(visit_info, "Processing " + idb_file)
            cd = os.path.dirname
            idb_domain = os.path.basename(cd(cd(idb_file)))
            idb_basename = os.path.basename(idb_file)
            url_idb_basename = "%s-%s" %\
                (fu.get_basename_from_url(visit_info.url,
                                          str(visit_info.rank)), idb_basename)
            dst_file = os.path.join(visit_info.out_dir, url_idb_basename)
            shutil.copy2(idb_file, dst_file)
            db_name = ""
            obj_stores = {}
            conn = sqlite3.connect(idb_file)
            with conn:
                c = conn.cursor()
                c.execute('select * from database;')
                rows = c.fetchall()
                for row in rows:
                    db_name = row[0]  # Column 0 is name

                c.execute('select * from object_store')
                rows = c.fetchall()
                for row in rows:
                    obj_stores[row[0]] = row[2]  # Column 0: id, column 2: name
                c.execute("select id, object_store_id, hex(key_value),"
                          "hex(data) from object_data;")
                rows = c.fetchall()
                idb_rows = [(obj_stores[row[1]], row[2], row[3])
                            for row in rows]
                # print_log(visit_info, "Processing %s" % len(idb_rows))
                return idb_domain, db_name, idb_rows
