############
Installation
############

.. |dob-prompt| replace:: ``dob-prompt``
.. _dob-prompt: https://github.com/tallybark/dob-prompt

.. |virtualenv| replace:: ``virtualenv``
.. _virtualenv: https://virtualenv.pypa.io/en/latest/

.. |workon| replace:: ``workon``
.. _workon: https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html?highlight=workon#workon

To install system-wide, run as superuser:

.. code-block:: sh

   $ pip3 install dob-prompt

To install user-local, simply run:

.. code-block:: sh

    $ pip3 install -U dob-prompt

To install within a |virtualenv|_, try:

.. code-block:: sh

    $ mkvirtualenv dob-prompt
    (dob-prompt) $ pip3 install dob-prompt

To develop on the project, link to the source files instead:

.. code-block:: sh

    (dob-prompt) $ deactivate
    $ rmvirtualenv dob-prompt
    $ git clone git@github.com:tallybark/dob-prompt.git
    $ cd dob-prompt
    $ mkvirtualenv -a $(pwd) --python=/usr/bin/python3.6 dob-prompt
    (dob-prompt) $ make develop

After creating the virtual environment,
to start developing from a fresh terminal, run |workon|_:

.. code-block:: sh

    $ workon dob-prompt
    (dob-prompt) $ ...

