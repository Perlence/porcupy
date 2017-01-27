Reference
=========

Porcupy compiler uses Python's `ast <https://docs.python.org/3/library/ast.html>`_ module to parse Porcupy scenarios.
Porcupy aims to resemble Python as close as possible, with some cues taken from Go.
But it's not feasible to implement each and every one of Python language features.

Here's a list of Python language features not supported in Porcupy:

- The import system

- Expressions:

  - Await expression
  - Power operator
  - Shifting operations
  - Binary bitwise operations
  - Conditional expressions
  - Lambdas
  - Keywords in function calls
  - ``list``, ``set``, ``dict``, and generator comprehensions

- Simple statements:

  - The ``assert`` statement
  - The ``del`` statement
  - The ``return`` statement
  - The ``yield`` statement
  - The ``raise`` statement
  - The ``import`` statement
  - The ``global`` statement
  - The ``nonlocal`` statement

- Compound statements:

  - The ``try`` statement
  - The ``with`` statement
  - Function definitions
  - Class definitions
  - Coroutines


Identifiers and assignment
--------------------------

Unlike Python, Porcupy introduces a distinction between variables and constants.
Constants are not assigned to in-game variables, like ``p1z``, the value of constant is stored only in compiler's memory.
To define a constant, write its name in upper case:

.. code-block:: python

   PUNCH_VELOCITY = 15

.. note::

   Because of the way the game parses floating point numbers, and because of the way Porcupy tries to alleviate it,
   defining floating point constants is not allowed.

All other names are considered variable names:

.. code-block:: python

   number = 0

Chained assignment and tuple unpacking are supported:

.. code-block:: python

   x = y = 0
   a, b = 1, 2

.. note::

   Although present in game, string variables are broken, and it's not possible to set a string to a variable.
   At the same time, it's still possible to define a string constant.


Data types
----------

Porcupy supports the following data types:

Numbers
   Integers

   Booleans

   Floating point numbers

Sequences
  All sequences provide a way to get/set an item by index, query the length and capacity.

  Immutable sequences
     Range
       See the :class:`range` built-in.

     Reversed
       See the :class:`reversed` built-in.

  Mutable sequences
     Lists
        The items of a list are of the same type and the number of items is constant and known at compile-time:

        .. code-block:: python

           x = [0, 1, 2, 3, 4]

        No original list methods are implemented in Porcupy lists, it can only be used to store a sequence of numbers, get
        and set them by index:

        .. code-block:: python

           x[0] = 10
           print(x[0])
           print(len(x))

        .. note::

           Negative indices are not supported.

     Slices
        Slice is a variable-length sequence with defined maximum capacity, backed by a list.
        Essentially, slice is a triple of values: address of first element, length of slice, capacity of slice.

        .. code-block:: python

           x = [0, 0, 0, 0, 0]  # a list of length 5
           s = x[:]  # a slice of list *x*, length 5, capacity 5
           s = x[1:]  # a slice of list *x*, length 4, capacity 4
           s = x[:0]  # a slice of list *x*, length 0, capacity 5
           s = x[1:3]  # a slice of list *x*, length 3, capacity 4

        .. note::

           Slice step is not supported.

        There's a very useful shorthand notation with :func:`slice`.

        It's possible to slice other slices:

        .. code-block:: python

           x = slice(int, 5)
           y = x[:3]

        Slices can be appended to:

        .. code-block:: python

           x = slice(int, 0, 5)
           x.append(4)

        .. warning::

           There's currently no mechanism to prevent user from appending an item to a "full" slice, so be sure to check
           length and capacity of slice before appending yourself.


Compound statements
-------------------

Only the following compound statements from Python are supported:

- The ``if`` statement
- The ``while`` statement
- The ``for`` statement

Each of them supports optional ``else`` clause.

The ``for`` statement differs a bit from the original.
It can be used to iterate lists, slices and ranges:

.. code-block:: python

   items = [10, 20, 30, 40]
   for item in items:
       print(item)  # prints '10', '20', '30', '40', one on each line

But it's also possible to access item's index without the ``enumerate`` function:

.. code-block:: python

   items = [10, 20, 30, 40]
   for i, item in items:
      print('{} {}'.format(i, item))  # prints '0 10', '1 20', and so on


Built-in functions
------------------

.. function:: cap(sequence) -> int

   Return the capacity of a given sequence.

   :param sequence: an instance of list, slice, range, or reversed.

.. function:: len(sequence) -> int

   Return the length of a given sequence.

   :param sequence: a list, slice, range, or reversed.

.. function:: load_map(map_name)

   Load the given map.

   .. note::

      This function works only in Yozhiks in Quake II v1.07.

.. function:: print(*values)

   Print *values* as a message in the top-left corner of the screen, separated by a single space.

.. function:: print_at(x, y, duration, *values)

   Print *values* in given point on screen for *duration* game ticks, separated by a single space.

   :param int x: *x* coordinate of message.
   :param int y: *y* coordinate of message.
   :param int duration: number of game ticks the message will be visible.
   :param values: parts of message to be printed.

   .. note::

      Only 20 such messages can be shown at a given time.

.. function:: randint(a, b) -> int

   Return a random integer *N* such that ``a <= N <= b``.

.. class:: range(stop) -> range object
.. class:: range(start, stop[, step]) -> range object

   Return an object that produces a sequence of integers from start (inclusive) to stop (exclusive) by step.

.. class:: reversed(sequence) -> reversed object

   Return a reverse sequence without allocating any in-game variables.

.. function:: set_color(r, g, b)

   Set color of :func:`print_at` messages.

.. function:: slice(type, len, cap=None) -> slice object

   Create a slice of capacity *cap* and *len* zero elements of given *type*.

   :param type: int, bool, or float.
   :param int len: length of slice to make.
   :param int cap: capacity of slice to make, defaults to *len*.

   .. code-block:: python

      x = slice(int, 5)  # equivalent to [0, 0, 0, 0, 0][:]
      x = slice(int, 1, 5)  # equivalent to [0, 0, 0, 0, 0][:1]
      y = slice(bool, 3)  # equivalent to [False, False, False][:]
      z = slice(float, 5)  # equivalent to [.0, .0, .0, .0, .0][:]


Game objects
------------

Porcupy provides access to many built-in objects to interact with the game.

.. data:: bots

   A list of 10 :class:`Bot` instances.

.. data:: buttons

   A list of 50 :class:`Button` instances.

.. data:: doors

   A list of 50 :class:`Door` instances.

.. data:: points

   A list of 100 :class:`Point` instances.

.. data:: system

   A single :class:`System` instance.

.. data:: timers

   A list of 100 :class:`Timer` instances.
   First timer ``timers[0]`` is always started with the game, so if it's necessary to set initial variables and game
   state, use this approach:

   .. code-block:: python

      if timers[0].value == 1:
          # Initialize here
          pass

.. data:: viewport

   A single :class:`Viewport` instance.

.. data:: yozhiks

   A list of 10 :class:`Yozhik` instances.
   First yozhik ``yozhiks[0]`` is player himself.

.. note::

   All classes below cannot be instantiated in scenario, and, in fact, they're not in the scope.

.. class:: Bot

   .. attribute:: ai

      (*bool*) -- should bot function on its own.

   .. attribute:: can_see_target

      (*bool*, *read-only*).

   .. attribute:: goto

      (:class:`Point`) -- make bot go to given :class:`Point`.

   .. attribute:: level

      (*int*) -- a level of the bot, see :ref:`list of bot level constants <bot-levels>` for possible values.

   .. attribute:: point

      (:class:`Point`, *read-only*) -- a :class:`Point` where bot is now.

   .. attribute:: target

      (:class:`Yozhik`) -- attack target of the bot.

.. class:: Button

   .. attribute:: is_pressed

      (*bool*, *read-only*).

   .. method:: press()

.. class:: Door


   .. attribute:: state

      (*int*, *read-only*) -- see :ref:`list of door state constants <door-states>` for possible values.

   .. method:: open()
   .. method:: close()

.. class:: Point

   Points are set in the map editor, and they are primarily used to tell a bot where to go.
   They can also be used to easily mark a location on map to serve as a trigger, or to display a message with
   :func:`print_at`.

   .. attribute:: pos_x

      (*int*) -- *x* coordinate of the point.

   .. attribute:: pos_y

      (*int*) -- *y* coordinate of the point.

.. class:: System

   .. attribute:: bots

      (*int*) -- number of bots.

   .. attribute:: color

      (*int*) -- color of :func:`print_at` messages.

      It's a triple of 8-bit integers packed in one: ``blue*65536 + green*256 + red``.
      It's easier to use :func:`set_color` instead of setting color value to this attribute.

      Default color is ``48128``, or ``rgb(0, 188, 0)``.

   .. attribute:: frag_limit

      (*int*) -- see :ref:`list of frag limit constants <frag-limits>` for possible values.

   .. attribute:: game_mode

      (*int*, *read-only*) -- current game mode, see :ref:`list of games modes <game-modes>` for possible values.

.. class:: Timer

   A timer object that counts game ticks.

   One game tick is roughly *1/50* of a second.

   .. attribute:: enabled

      (*bool*) -- is the timer ticking.

   .. attribute:: value

      (*int*) -- how much ticks did the timer count.

   .. method:: start()
   .. method:: stop()

.. class:: Viewport

   Viewport object holds the location of top-left game screen corner in relation to top-left map corner.

   .. attribute:: pos_x

      (*int*) -- *x* coordinate of top-left screen corner.

   .. attribute:: pos_y

      (*int*) -- *y* coordinate of top-left screen corner.

.. class:: Yozhik

   .. attribute:: ammo

      (*int*) -- amount of ammo for current weapon.

   .. attribute:: armor

      (*int*) -- armor points.

   .. attribute:: frags

      (*int*) -- number of frags.

   .. attribute:: is_weapon_in_inventory

      (*bool*) -- setting :attr:`is_weapon_in_inventory` to ``True`` places current weapon in yozhik's inventory.

   .. attribute:: health

      (*int*) -- health points.

   .. attribute:: pos_x

      (*float*) -- *x* coordinate of yozhik's position.

   .. attribute:: pos_y

      (*float*) -- *y* coordinate of yozhik's position.

   .. attribute:: speed_x

      (*float*) -- *x* coordinate of yozhik's speed vector.

   .. attribute:: speed_y

      (*float*) -- *y* coordinate of yozhik's speed vector.

   .. attribute:: team

      (*int*) -- number of team.

   .. attribute:: view_angle

      (*int*) -- a value in range ``[0, 127]``, when yozhik looks up it's 0, when he looks straight to the right
      or left it's 64, when he looks down it's 127.

   .. attribute:: weapon

      (*int*) -- current weapon, see :ref:`list of weapon constants <weapons>`.
      Setting value to this attribute makes yozhik switch to the weapon, but does not place it in his inventory.
      If he didn't have it before and switches back, the weapon will be gone, unless :attr:`~Yozhik.is_weapon_in_inventory` was set.

   .. method:: spawn(point: int)

     Spawn yozhik in the given spawn-point.

     Spawn points are enumerated starting at 1, from top to bottom, left to right:

     .. image:: images/spawn-points.png


Constants
---------

.. _weapons:

Weapons:
   .. data:: W_BFG10K(0)
   .. data:: W_BLASTER(1)
   .. data:: W_SHOTGUN(2)
   .. data:: W_SUPER_SHOTGUN(3)
   .. data:: W_MACHINE_GUN(4)
   .. data:: W_CHAIN_GUN(5)
   .. data:: W_GRENADE_LAUNCHER(6)
   .. data:: W_ROCKET_LAUNCHER(7)
   .. data:: W_HYPERBLASTER(8)
   .. data:: W_RAILGUN(9)

.. _door-states:

Door states:
   .. data:: DS_CLOSED(0)
   .. data:: DS_OPEN(1)
   .. data:: DS_OPENING(2)
   .. data:: DS_CLOSING(3)

.. _frag-limits:

Frag limits:
   .. data:: FL_10(0)
   .. data:: FL_20(1)
   .. data:: FL_30(2)
   .. data:: FL_50(3)
   .. data:: FL_100(4)
   .. data:: FL_200(5)

.. _bot-levels:

Bot levels:
   .. data:: BL_VERY_EASY(0)
   .. data:: BL_EASY(1)
   .. data:: BL_NORMAL(2)
   .. data:: BL_HARD(3)
   .. data:: BL_IMPOSSIBLE(4)

.. _game-modes:

Game modes:
   .. data:: GM_MULTI_LAN(0)
   .. data:: GM_MULTI_DUEL(1)
   .. data:: GM_HOT_SEAT(2)
   .. data:: GM_MENU(3)
   .. data:: GM_SINGLE(4)
   .. data:: GM_SHEEP(5)
   .. data:: GM_HOT_SEAT_SPLIT(6)
