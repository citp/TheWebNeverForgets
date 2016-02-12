from __future__ import division
import commands
import hashlib
import signal
from random import choice
from crawler.common import TimeExceededError


ASCII_LOWERCASE_CHARS = 'abcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'

DEFAULT_RAND_STR_SIZE = 6
DEFAULT_RAND_STR_CHARS = ASCII_LOWERCASE_CHARS + DIGITS


def rand_str(size=DEFAULT_RAND_STR_SIZE, chars=DEFAULT_RAND_STR_CHARS):
    """Return random string given a size and character space."""
    return ''.join(choice(chars) for _ in range(size))


def hash_text(text, algo='sha256'):
    """Hash the given text."""
    h = hashlib.new(algo)
    h.update(text)
    return h.hexdigest()


def raise_signal(signum, frame):
    raise TimeExceededError


def timeout(duration):
    """Timeout after given duration."""
    # SIGALRM is only available on Linux
    signal.signal(signal.SIGALRM, raise_signal)
    signal.alarm(duration)  # alarm after X seconds


def cancel_timeout():
    signal.alarm(0)


def run_cmd(cmd):
    return commands.getstatusoutput('%s ' % (cmd))
