Library reference
=================

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

   .. important::

      This function works only in Yozhiks in Quake II v1.07.

.. function:: print(value)

   Print the value as a message.

.. function:: print_at(x, y, dur, value)

   Print the value in given point on screen for *dur* game ticks.

   :param int x: *x* coordinate of message.
   :param int y: *y* coordinate of message.
   :param int dur: number of game ticks the message will be visible.
   :param value: message to be printed.

   .. important::

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

.. data:: buttons

   A list of 50 :class:`Button` instances.

.. class:: Button

   :param bool is_pressed: (*read-only*).

   .. method:: press()


.. data:: doors

   A list of 50 :class:`Door` instances.

.. class:: Door

   :param int state: (*read-only*).

   .. method:: open()
   .. method:: close()


.. data:: points

   A list of 100 :class:`Point` instances.

.. class:: Point

   Points are set in the map editor, and they are primarily used to tell a bot where to go.
   They can also be used to easily mark a location on map to serve like a trigger, or to display a message with
   :func:`print_at`.

   :param int pos_x: *x* coordinate of the point.
   :param int pos_y: *y* coordinate of the point.


.. data:: system

   A single :class:`System` instance.

.. class:: System

   :param int bots: number of bots.
   :param int color: color of :meth:`print_at` messages.
   :param int frag_limit:
   :param int game_mode: current game mode (*read-only*).


.. data:: timers

   A list of 100 :class:`Timer` instances.
   First timer ``timers[0]`` is always started with the game, so if it's necessary to set initial variables and game
   state, use this approach:

   .. code-block:: python

      if timers[0].value == 1:
          # Initialize here
          pass

.. class:: Timer

   A timer object that counts game ticks.

   One game tick is roughly *1/50* of a second.

   :param int value: how much ticks did the timer count.
   :param bool enabled: is the timer going.

   .. method:: start()
   .. method:: stop()


.. data:: viewport

   A single :class:`Viewport` instance.

.. class:: Viewport

   Viewport object holds the location of top-left game screen corner in relation to top-left map corner.

   :param int pos_x: *x* coordinate of top-left screen corner.
   :param int pos_y: *y* coordinate of top-left screen corner.


.. data:: yozhiks

   A list of 10 :class:`Yozhik` instances.

.. class:: Yozhik

   :param int frags: number of frags.
   :param float pos_x: *x* coordinate of yozhik's position.
   :param float pos_y: *y* coordinate of yozhik's position.
   :param float speed_x: *x* coordinate of yozhik's speed vector.
   :param float speed_y: *y* coordinate of yozhik's speed vector.
   :param int health: health points.
   :param int armor: armor points.
   :param bool has_weapon: setting :attr:`has_weapon` to ``True`` makes yozhik switch to the weapon, last set to
      :attr:`weapon` attribute.
   :param int weapon: setting value to this attribute give yozhik a weapon.
   :param int ammo: amount of ammo for current weapon.
   :param int view_angle: a value in range *[0, 127]*, when yozhik looks up it's 0, when he looks straight to the right
      or left it's 64, when he looks down it's 127.
   :param int team: number of team.

   .. method:: spawn(point: int)

     Spawn yozkik given spawn-point.

     Spawn points are enumerated starting at 1, from top-left to
     bottom-right.
