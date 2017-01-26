Introduction
============

`Yozhiks in Quake II <http://gegames.org/>`_ is video game developed by `Nick Koleda <http://twitter.com/zyaleniyeg>`_
between 2001-2006.
It's a 2D side-scrolling demake of *Quake II* where player controls a *yozhik* (hedgehog) battling other yozhiks.
It features single player with bots, hot seat, LAN and Internet multiplayer games with following game modes: Deathmatch,
Team Deathmatch, Capture the Flag, Points, Scenario.
There is a map editor to create and edit maps.

The game gained a short-lived fan following in Russia and influenced *3d[Power]* to create `NFK <http://needforkill.ru/>`_.

More interestingly it features a tiny custom-made programming language to write *scenarios* attached to a map.
With this language, map designer is able to create scripted events, spawn and control bots, access and modify the state
of game objects like doors, buttons, and other players.

However, the code is pretty arcane:

.. _spawn-scenario:
.. code-block:: none

   # e1p < 1 ( p1z ~5  p1z p1z+1  e1b ^1  e1p 125 )

It reads like this: if first yozhik has less health points than 1, then spawn him in a random spawn-point between 1 and
5, and give him 125 health points.

As you can see, reading and writing such code is not an easy feat: arbitrary one-letter abbreviations of methods and
properties, unnamed variables, flow control consists of one-level ``if`` statement and ``goto`` statement.

Head over to :doc:`quickstart` and learn how to install and write scenarios in Porcupy.
