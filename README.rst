======
stopit
======

Raise asynchronous exceptions in other threads, control the timeout of
blocks or callables with two context managers and two decorators.

.. attention:: API Changes

   Users of 1.0.0 should upgrade their source code:

   - ``stopit.Timeout`` is renamed ``stopit.ThreadingTimeout``
   - ``stopit.timeoutable`` is renamed ``stopit.threading_timeoutable``

   Explications follow below...

.. contents::

Overview
========

This module provides:

- a function that raises an exception in another thread, including the main
  thread.

- two context managers that may stop its inner block activity on timeout.

- two decorators that may stop its decorated callables on timeout.

Developed and tested with CPython 2.6, 2.7, 3.3 and 3.4 on MacOSX. Should work
on any OS (xBSD, Linux, Windows) except when explicitly mentioned.

.. note::

   Signal based timeout controls, namely ``SignalTimeout`` context manager and
   ``signal_timeoutable`` decorator won't work in Windows that has no support
   for ``signal.SIGALRM``. Any help to work around this is welcome.

Installation
============

Using ``stopit`` in your application
------------------------------------

Both work identically:

.. code:: bash

  easy_install stopit
  pip install stopit

Developing ``stopit``
---------------------

.. code:: bash

  # You should prefer forking if you have a Github account
  git clone https://github.com/glenfant/stopit.git
  cd stopit
  python setup.py develop

  # Does it work for you ?
  python setup.py test

Public API
==========

Exception
---------

``stopit.TimeoutException``
...........................

A ``stopit.TimeoutException`` may be raised in a timeout context manager
controlled block.

This exception may be propagated in your application at the end of execution
of the context manager controlled block, see the ``swallow_ex`` parameter of
the context managers.

Note that the ``stopit.TimeoutException`` is always swallowed after the
execution of functions decorated with ``xxx_timeoutable(...)``. Anyway, you
may catch this exception **within** the decorated function.

Threading based resources
-------------------------

.. warning::

   Threading based resources will only work with CPython implementations
   since we use CPython specific low level API. This excludes Iron Python,
   Jython, Pypy, ...

   Will not stop the execution of blocking Python atomic instructions that
   acquire the GIL. In example, if the destination thread is actually
   executing a ``time.sleep(20)``, the asynchronous exception is effective
   **after** its execution.

``stopit.async_raise``
......................

A function that raises an arbitrary exception in another thread

``async_raise(tid, exception)``

- ``tid`` is the thread identifier as provided by the ``ident`` attribute of a
  thread object. See the documentation of the ``threading`` module for further
  information.

- ``exception`` is the exception class or object to raise in the thread.

``stopit.ThreadingTimeout``
...........................

A context manager that "kills" its inner block execution that exceeds the
provided time.

``ThreadingTimeout(seconds, swallow_exc=True)``

- ``seconds`` is the number of seconds allowed to the execution of the context
  managed block.

- ``swallow_exc`` : if ``False``, the possible ``stopit.TimeoutException`` will
  be re-raised when quitting the context managed block. **Attention**: a
  ``True`` value does not swallow other potential exceptions.

**Methods and attributes**

of a ``stopit.ThreadingTimeout`` context manager.

.. list-table::
   :header-rows: 1

   * - Method / Attribute
     - Description

   * - ``.cancel()``
     - Cancels the timeout control. This method is intended for use within the
       block that's under timeout control, specifically to cancel the timeout
       control. Means that all code executed after this call may be executed
       till the end.

   * - ``.state``
     - This attribute indicated the actual status of the timeout control. It
       may take the value of the ``EXECUTED``, ``EXECUTING``, ``TIMED_OUT``,
       ``INTERRUPTED`` or ``CANCELED`` attributes. See below.

   * - ``.EXECUTING``
     - The timeout control is under execution. We are typically executing
       within the code under control of the context manager.

   * - ``.EXECUTED``
     - Good news: the code under timeout control completed normally within the
       assigned time frame.

   * - ``.TIMED_OUT``
     - Bad news: the code under timeout control has been sleeping too long.
       The objects supposed to be created or changed within the timeout
       controlled block should be considered as non existing or corrupted.
       Don't play with them otherwise informed.

   * - ``.INTERRUPTED``
     - The code under timeout control may itself raise explicit
       ``stopit.TimeoutException`` for any application logic reason that may
       occur. This intentional exit can be spotted from outside the timeout
       controlled block with this state value.

   * - ``.CANCELED``
     - The timeout control has been intentionally canceled and the code
       running under timeout control did complete normally. But perhaps after
       the assigned time frame.


A typical usage:

.. code:: python

   import stopit
   # ...
   with stopit.ThreadingTimeout(10) as to_ctx_mgr:
       assert to_ctx_mgr.state == to_ctx_mgr.EXECUTING
       # Something potentially very long but which
       # ...

   # OK, let's check what happened
   if to_ctx_mgr.state == to_ctx_mgr.EXECUTED:
       # All's fine, everything was executed within 10 seconds
   elif to_ctx_mgr.state == to_ctx_mgr.EXECUTING:
       # Hmm, that's not possible outside the block
   elif to_ctx_mgr.state == to_ctx_mgr.TIMED_OUT:
       # Eeek the 10 seconds timeout occurred while executing the block
   elif to_ctx_mgr.state == to_ctx_mgr.INTERRUPTED:
       # Oh you raised specifically the TimeoutException in the block
   elif to_ctx_mgr.state == to_ctx_mgr.CANCELED:
       # Oh you called to_ctx_mgr.cancel() method within the block but it
       # executed till the end
   else:
       # That's not possible

Notice that the context manager object may be considered as a boolean
indicating (if ``True``) that the block executed normally:

.. code:: python

   if to_ctx_mgr:
       # Yes, the code under timeout control completed
       # Objects it created or changed may be considered consistent

``stopit.threading_timeoutable``
................................

A decorator that kills the function or method it decorates, if it does not
return within a given time frame.

``stopit.threading_timeoutable([default [, timeout_param]])``

- ``default`` is the value to be returned by the decorated function or method of
  when its execution timed out, to notify the caller code that the function
  did not complete within the assigned time frame.

  If this parameter is not provided, the decorated function or method will
  return a ``None`` value when its execution times out.

  .. code:: python

     @stopit.threading_timeoutable(default='not finished')
     def infinite_loop():
         # As its name says...

     result = infinite_loop(timeout=5)
     assert result == 'not finished'

- ``timeout_param``: The function or method you have decorated may require a
  ``timeout`` named parameter for whatever reason. This empowers you to change
  the name of the ``timeout`` parameter in the decorated function signature to
  whatever suits, and prevent a potential naming conflict.

  .. code:: python

     @stopit.threading_timeoutable(timeout_param='my_timeout')
     def some_slow_function(a, b, timeout='whatever'):
         # As its name says...

     result = some_slow_function(1, 2, timeout="something", my_timeout=2)


About the decorated function
............................

or method...

As you noticed above, you just need to add the ``timeout`` parameter when
calling the function or method. Or whatever other name for this you chose with
the ``timeout_param`` of the decorator. When calling the real inner function
or method, this parameter is removed.


Signaling based resources
-------------------------

.. warning::

   Using signaling based resources will **not** work under Windows or any OS
   that's not based on Unix.

``stopit.SignalTimeout`` and ``stopit.signal_timeoutable`` have exactly the
same API as their respective threading based resources, namely
`stopit.ThreadingTimeout`_ and `stopit.threading_timeoutable`_.

See the `comparison chart`_ that warns on the more or less subtle differences
between the `Threading based resources`_ and the `Signaling based resources`_.

Logging
-------

The ``stopit`` named logger emits a warning each time a block of code
execution exceeds the associated timeout. To turn logging off, just:

.. code:: python

   import logging
   stopit_logger = logging.getLogger('stopit')
   stopit_logger.seLevel(logging.ERROR)

.. _comparison chart:

Comparing thread based and signal based timeout control
-------------------------------------------------------

.. list-table::
   :header-rows: 1

   * - Feature
     - Threading based resources
     - Signaling based resources

   * - GIL
     - Can't interrupt a long Python atomic instruction. e.g. if
       ``time.sleep(20.0)`` is actually executing, the timeout will take
       effect at the end of the execution of this line.
     - Don't care of it

   * - Thread safety
     - **Yes** : Thread safe as long as each thread uses its own ``ThreadingTimeout``
       context manager or ``threading_timeoutable`` decorator.
     - **Not** thread safe. Could yield unpredictable results in a
       multithreads application.

   * - Nestable context managers
     - **Yes** : you can nest threading based context managers
     - **No** : never nest a signaling based context manager in another one.
       The innermost context manager will automatically cancel the timeout
       control of outer ones.

   * - Accuracy
     - Any positive floating value is accepted as timeout value. The accuracy
       depends on the GIL interval checking of your platform. See the doc on
       ``sys.getcheckinterval`` and ``sys.setcheckinterval`` for your Python
       version.
     - Due to the use of ``signal.SIGALRM``, we need provide an integer number
       of seconds. So a timeout of ``0.6`` seconds will ve automatically
       converted into a timeout of zero second!

   * - Supported platforms
     - Any CPython 2.6, 2.7 or 3.3 on any OS with threading support.
     - Any Python 2.6, 2.7 or 3.3 with ``signal.SIGALRM`` support. This
       excludes Windows boxes

Known issues
============

Timeout accuracy
----------------

**Important**: the way CPython supports threading and asynchronous features has
impacts on the accuracy of the timeout. In other words, if you assign a 2.0
seconds timeout to a context managed block or a decorated callable, the
effective code block / callable execution interruption may occur some
fractions of seconds after this assigned timeout.

For more background about this issue - that cannot be fixed - please read
Python gurus thoughts about Python threading, the GIL and context switching
like these ones:

- http://pymotw.com/2/threading/
- https://wiki.python.org/moin/GlobalInterpreterLock

This is the reason why I am more "tolerant" on timeout accuracy in the tests
you can read thereafter than I should be for a critical real-time application
(that's not in the scope of Python).

It is anyway possible to improve this accuracy at the expense of the global
performances decreasing the check interval which defaults to 100. See:

- https://docs.python.org/2.7/library/sys.html#sys.getcheckinterval
- https://docs.python.org/2.7/library/sys.html#sys.getcheckinterval

If this is a real issue for users (want a precise timeout and not an
approximative one), a future release will add the optional ``check_interval``
parameter to the context managers and decorators. This parameter will enable
to lower temporarily the threads switching check interval, having a more
accurate timeout at the expense of the overall performances while the context
managed block or decorated functions are executing.

``gevent`` support
------------------

Threading timeout control as mentioned in `Threading based resources`_ does not work as expected
when used in the context of a gevent worker.

See the discussion in `Issue 13 <https://github.com/glenfant/stopit/issues/13>`_ for more details.

Tests and demos
===============

.. code:: pycon

   >>> import threading
   >>> from stopit import async_raise, TimeoutException

In a real application, you should either use threading based timeout resources:

.. code:: pycon

   >>> from stopit import ThreadingTimeout as Timeout, threading_timeoutable as timeoutable  #doctest: +SKIP

Or the POSIX signal based resources:

.. code:: pycon

   >>> from stopit import SignalTimeout as Timeout, signal_timeoutable as timeoutable  #doctest: +SKIP

Let's define some utilities:

.. code:: pycon

   >>> import time
   >>> def fast_func():
   ...     return 0
   >>> def variable_duration_func(duration):
   ...     t0 = time.time()
   ...     while True:
   ...         dummy = 0
   ...         if time.time() - t0 > duration:
   ...             break
   >>> exc_traces = []
   >>> def variable_duration_func_handling_exc(duration, exc_traces):
   ...     try:
   ...         t0 = time.time()
   ...         while True:
   ...             dummy = 0
   ...             if time.time() - t0 > duration:
   ...                 break
   ...     except Exception as exc:
   ...         exc_traces.append(exc)
   >>> def func_with_exception():
   ...     raise LookupError()

``async_raise`` function raises an exception in another thread
--------------------------------------------------------------

Testing ``async_raise()`` with a thread of 5 seconds:

.. code:: pycon

   >>> five_seconds_threads = threading.Thread(
   ...     target=variable_duration_func_handling_exc, args=(5.0, exc_traces))
   >>> start_time = time.time()
   >>> five_seconds_threads.start()
   >>> thread_ident = five_seconds_threads.ident
   >>> five_seconds_threads.is_alive()
   True

We raise a LookupError in that thread:

.. code:: pycon

   >>> async_raise(thread_ident, LookupError)

Okay but we must wait few milliseconds the thread death since the exception is
asynchronous:

.. code:: pycon

   >>> while five_seconds_threads.is_alive():
   ...     pass

And we can notice that we stopped the thread before it stopped by itself:

.. code:: pycon

   >>> time.time() - start_time < 0.5
   True
   >>> len(exc_traces)
   1
   >>> exc_traces[-1].__class__.__name__
   'LookupError'

``Timeout`` context manager
---------------------------

The context manager stops the execution of its inner block after a given time.
You may manage the way the timeout occurs using a ``try: ... except: ...``
construct or by inspecting the context manager ``state`` attribute after the
block.

Swallowing Timeout exceptions
.............................

We check that the fast functions return as outside our context manager:

.. code:: pycon

   >>> with Timeout(5.0) as timeout_ctx:
   ...     result = fast_func()
   >>> result
   0
   >>> timeout_ctx.state == timeout_ctx.EXECUTED
   True

And the context manager is considered as ``True`` (the block executed its last
line):

.. code:: pycon

   >>> bool(timeout_ctx)
   True

We check that slow functions are interrupted:

.. code:: pycon

   >>> start_time = time.time()
   >>> with Timeout(2.0) as timeout_ctx:
   ...     variable_duration_func(5.0)
   >>> time.time() - start_time < 2.2
   True
   >>> timeout_ctx.state == timeout_ctx.TIMED_OUT
   True

And the context manager is considered as ``False`` since the block did timeout.

.. code:: pycon

   >>> bool(timeout_ctx)
   False

Other exceptions are propagated and must be treated as usual:

.. code:: pycon

   >>> try:
   ...     with Timeout(5.0) as timeout_ctx:
   ...         result = func_with_exception()
   ... except LookupError:
   ...     result = 'exception_seen'
   >>> timeout_ctx.state == timeout_ctx.EXECUTING
   True
   >>> result
   'exception_seen'

Propagating ``TimeoutException``
................................

We can choose to propagate the ``TimeoutException`` too. Potential exceptions
have to be handled:

.. code:: pycon

   >>> result = None
   >>> start_time = time.time()
   >>> try:
   ...     with Timeout(2.0, swallow_exc=False) as timeout_ctx:
   ...         variable_duration_func(5.0)
   ... except TimeoutException:
   ...     result = 'exception_seen'
   >>> time.time() - start_time < 2.2
   True
   >>> result
   'exception_seen'
   >>> timeout_ctx.state == timeout_ctx.TIMED_OUT
   True

Other exceptions must be handled too:

.. code:: pycon

   >>> result = None
   >>> start_time = time.time()
   >>> try:
   ...     with Timeout(2.0, swallow_exc=False) as timeout_ctx:
   ...         func_with_exception()
   ... except Exception:
   ...     result = 'exception_seen'
   >>> time.time() - start_time < 0.1
   True
   >>> result
   'exception_seen'
   >>> timeout_ctx.state == timeout_ctx.EXECUTING
   True

``timeoutable`` callable decorator
----------------------------------

This decorator stops the execution of any callable that should not last a
certain amount of time.

You may use a decorated callable without timeout control if you don't provide
the ``timeout`` optional argument:

.. code:: pycon

   >>> @timeoutable()
   ... def fast_double(value):
   ...     return value * 2
   >>> fast_double(3)
   6

You may specify that timeout with the ``timeout`` optional argument.
Interrupted callables return None:

.. code:: pycon

   >>> @timeoutable()
   ... def infinite():
   ...     while True:
   ...         pass
   ...     return 'whatever'
   >>> infinite(timeout=1) is None
   True

Or any other value provided to the ``timeoutable`` decorator parameter:

.. code:: pycon

   >>> @timeoutable('unexpected')
   ... def infinite():
   ...     while True:
   ...         pass
   ...     return 'whatever'
   >>> infinite(timeout=1)
   'unexpected'

If the ``timeout`` parameter name may clash with your callable signature, you
may change it using ``timeout_param``:

.. code:: pycon

   >>> @timeoutable('unexpected', timeout_param='my_timeout')
   ... def infinite():
   ...     while True:
   ...         pass
   ...     return 'whatever'
   >>> infinite(my_timeout=1)
   'unexpected'

It works on instance methods too:

.. code:: pycon

   >>> class Anything(object):
   ...     @timeoutable('unexpected')
   ...     def infinite(self, value):
   ...         assert type(value) is int
   ...         while True:
   ...             pass
   >>> obj = Anything()
   >>> obj.infinite(2, timeout=1)
   'unexpected'

Links
=====

Source code (clone, fork, ...)
  https://github.com/glenfant/stopit

Issues tracker
  https://github.com/glenfant/stopit/issues

PyPI
  https://pypi.python.org/pypi/stopit

Credits
=======

- This is a NIH package which is mainly a theft of `Gabriel Ahtune's recipe
  <http://gahtune.blogspot.fr/2013/08/a-timeout-context-manager.html>`_ with
  tests, minor improvements and refactorings, documentation and setuptools
  awareness I made since I'm somehow tired to copy/paste this recipe among
  projects that need timeout control.

- `Gilles Lenfant <gilles.lenfant@gmail.com>`_: package creator and
  maintainer.

License
=======

This software is open source delivered under the terms of the MIT license. See the ``LICENSE`` file of this repository.