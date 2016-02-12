import unittest
import subprocess
from time import sleep
import utils.file_utils as fu
import crawler.ffmod as ffm
import sttest
SYS_CALLS = ["open", "read", "write"]


class Test(sttest.STTest):
        def test_simple_trace(self):
            sys_log_file = open(self.vi.sys_log, "w")
            subprocess.Popen("strace ls",
                             stderr=sys_log_file, stdout=sys_log_file,
                             shell=True)
            sys_log_file.close()
            sleep(5)  # wait for strace output to be available
            sys_logs = fu.read_file(self.vi.sys_log)
            for sys_call in SYS_CALLS:
                self.assertIn(sys_call, sys_logs)

        def test_attach_trace(self):
            sys_log_file = open(self.vi.sys_log, "w")
            vdisplay = ffm.start_xvfb()
            driver, _, proc = ffm.get_browser(self.vi.ff_log)
            subprocess.Popen("strace -p %d" % proc.pid,
                             stderr=sys_log_file, stdout=sys_log_file,
                             shell=True)
            driver.get("https://google.com")
            sleep(1)
            driver.close()
            proc.terminate()
            driver.quit()
            ffm.stop_xvfb(vdisplay)
            sys_log_file.close()
            sleep(5)  # wait for strace output to be available
            sys_logs = fu.read_file(self.vi.sys_log)
            for sys_call in SYS_CALLS:
                self.assertIn(sys_call, sys_logs,
                              """Cannot trace process, make sure you set up
                    ptrace permissions in /proc/sys/kernel/yama/ptrace_scope as
                    described in etc/setup.sh.""")


if __name__ == "__main__":
    unittest.main()
