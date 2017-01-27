Language reference
==================

Porcupy compiler uses Python's `ast <https://docs.python.org/3/library/ast.html>`_ module to parse Porcupy scenarios.
Porcupy aims to resemble Python as close, as possible, with some cues taken from Go.
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

The ``for`` statement differs a bit from original.
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
