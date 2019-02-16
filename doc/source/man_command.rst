.. _man-command:

|project|
=========

Synopsis
--------

|project_bold| [*options*]

Description
-----------

.. include:: description.inc

If not specified via a command line argument, |project_program| looks for a default configuration at :file:`/etc/autosuspend.conf`.
:manpage:`autosuspend.conf(5)` describes the configuration file, the available checks, and their configuration options.

Options
-------

.. program:: autosuspend

.. option:: -h, --help

   Displays an online help.

.. option:: -c FILE, --config FILE

   Specifies an alternate config file to use instead of the default on at :file:`/etc/autosuspend.conf`.

.. option:: -l FILE, --logging FILE

   Configure the logging system with the provided logging file.
   This file needs to follow the conventions for :ref:`Python logging files <python:logging-config-fileformat>`.

.. option:: -d

   Configure full debug logging in the command line.
   Mutually exclusive to :option:`autosuspend -l`.

Subcommand ``daemon``
~~~~~~~~~~~~~~~~~~~~~

Starts the continuously running daemon.

.. program:: autosuspend daemon

.. option:: -a, --allchecks

   Usually, |project_program| stops checks in each iteration as soon as the first matching check indicates system activity.
   If this flag is set, all subsequent checks are still executed.
   Useful mostly for debugging purposes.

.. option:: -r SECONDS, --runfor SECONDS

   If specified, do not run endlessly.
   Instead, operate only for the specified amount of seconds, then exit.
   Useful mostly for debugging purposes.

Subcommand ``presuspend``
~~~~~~~~~~~~~~~~~~~~~~~~~

Should be called by the system before suspending.

.. program:: autosuspend presuspend

No options

Bugs
----

Please report bugs at the project repository at https://github.com/languitar/autosuspend.

See also
--------

:manpage:`autosuspend.conf(5)`
