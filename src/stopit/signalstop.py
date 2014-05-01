# -*- coding: utf-8 -*-
"""
This recipe provides a context manager that stops the execution of its inner
code block after the timeout is gone. This recipe is stolen with some changes
and rewording in a less app centric vocabulary from the "rq" package.

https://github.com/glenfant/rq/blob/master/rq/timeouts.py.

Warnings:

- This does not work with Windows that does not handle the signals we need.

- This is not thead safe since the signal will get caught by a random thread.

- Tested on MacOSX with Python 2.6, 2.7 and 3.3 (may or not work eslsewhere)
"""
import signal

from .utils import TimeoutException, BaseTimeout, base_timeoutable


class SignalTimeout(BaseTimeout):
    def __init__(self, seconds, swallow_exc=True):
        """
        :param timeout: seconds enabled for processing the block under
          our context manager
        :param swallow_exception: do not spread the exception on timeout
        """
        seconds = int(seconds)  # alarm delay for signal MUST be int
        super(SignalTimeout, self).__init__(seconds, swallow_exc)

    def handle_timeout(self, signum, frame):
        self.state = BaseTimeout.TIMED_OUT
        raise TimeoutException('Block exceeded maximum timeout '
                               'value (%d seconds).' % self.seconds)

    # Required overrides
    def setup_interrupt(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def suppress_interrupt(self):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)


class signal_timeoutable(base_timeoutable):  #noqa
    """A function or method decorator that raises a ``TimeoutException`` to
    decorated functions that should not last a certain amount of time.
    this one uses ``ThreadingTimeout`` context manager.

    See :class:`.utils.base_timoutable`` class for further comments.
    """
    to_ctx_mgr = SignalTimeout

