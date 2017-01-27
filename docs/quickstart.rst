Quickstart
==========

Installation
------------

First of all, you must visit `Yozhiks in Quake II <http://gegames.org/>`_ and download the `game
<http://octagram.name/pub/gegames/egiki.1.06.rar.exe>`_ and `map editor
<http://octagram.name/pub/gegames/egiki.editor.exe>`_.

Make sure you have Python 3, then use *pip* to acquire the package:

.. code-block:: bash

   pip3 install 'git+https://github.com/Perlence/porcupy#egg=porcupy'


First scenario
--------------

Let's consider rewriting an :ref:`example <spawn-scenario>` from :doc:`intro` in Porcupy:

.. code-block:: python

   PLAYER = yozhiks[0]

   if PLAYER.health < 1:
       PLAYER.spawn(randint(1, 5))
       PLAYER.health = 125

List :data:`yozhiks` is a zero-indexed list of all yozhiks in the game and each of them has attributes like
:attr:`~Yozhik.health` and :attr:`~Yozhik.weapon`, and methods like :meth:`~Yozhik.spawn`.

Names written in upper case are considered constants, so, roughly speaking, each next occurrence of ``PLAYER`` after first
line will be replaced by ``yozhiks[0]``.

New built-in function :func:`randint` returns random integer in range ``[a, b]``, including both end points.

Let's save the scenario in a file, e.g. ``handicap_spawn.py``, and see what Porcupy compiler will produce:

.. code-block:: bash

   porcupy -i handicap_spawn.py

The result is:

.. code-block:: none

   # e1p >= 1 ( g1z ) p1z ~5 p2z p1z+1 e1b ^2 e1p 125 :1

It looks a lot like the original example, but you can notice new words like ``g1z`` and ``:1`` --- these are *goto*
statement and *goto* label respectively.

Now, the scenario on it's own is useless unless it's bundled with a map.
Go to directory where you installed Yozhiks in Quake II and the map editor.
Start ``red_egiks.exe``, open file ``MAPS/ArenaDM.egm``, change the name of map in *Info* dialog, and save it to
``MAPS/ArenaDM2.egm``.

Now we can compile and attach the Porcupy scenario to the map:

.. code-block:: bash

   porcupy -i handicap_spawn.py -a ArenaDM2.egm

Check if scenario works properly by loading the map in Yozhiks in Quake II and proceed to :doc:`language`.
