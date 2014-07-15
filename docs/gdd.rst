***************
Game Design Doc
***************

Intro
=====

Character Bios
==============

Rough Plot
==========

Gameplay Description
====================

Overview
--------

The game will be broken up into three game modes:

#. Assignment: A single battle
#. Exam: A set of three battles (two normal and a "miniboss")
#. Final: A set of nine battles broken down as follows:

   #. Regular Battle
   #. Regular Battle
   #. Regular Battle
   #. Miniboss (Checkpoint)
   #. Regular Battle
   #. Regular Battle
   #. Regular Battle
   #. Miniboss (Checkpoint)
   #. Boss

   After a checkpoint battle, the player can exit the exam and return to it later.
   Likewise, if a player loses a battle in the final, they can continue from their last checkpoint.

The goal of the game is to get strong enough from assignments and exams to defeat the final.
To get stronger, players can gain levels and equipment.

Character Stats
---------------

Characters have the following stats:

* Damage -- Their base damage in combat
* Movement -- How many squares the character can move
* Range -- How many squares away the character can attack

Combat
------

The combat will be a tactical combat style similar to `Final Fantasy Tactics <https://en.wikipedia.org/wiki/Final_Fantasy_Tactics>`_.
If the player reaches zero health they lose.
If all enemy combatants reach zero health, the player wins.

At the start of the player turn, they select a stance.
Afterwards, they can do any combination of moving and attacking.
The amount a player can move is dependent on their movement score.
A player can only attack once per turn.

.. note::
    We need to figure out turn order.
    Is this initiative based?
    ATB?

Spells/Stances
--------------

Instead of traditional spells, players will have "stances."
These stances can have either a positive ("benefit") or negative ("cost") affect on any of the following player stats:

* Damage
* Health over time
* Movement
* Range

A player keeps a catalog of stances in a spellbook, but must choose four stances before entering battle.

Spell Generation
----------------

Equipment
---------

Artistic Style Outline
======================

Systematic Breakdown of Components
==================================

Asset Break Down
================

Art
---

Characters
^^^^^^^^^^
* Player Character
* Enemy Character

Levels
^^^^^^
* ?

UI
^^
* Dialog Background

Audio
-----
* Combat BGM
* Title BGM
* Lobby/PreGame BGM
* UI Accept
* UI Decline

Suggested Game Flow Diagram
===========================

..
    .. uml::
    
        start
    
        if (Title Screen) then (New Character)
            :Character Creation;
        else (Load Character)
            :Character Load Screen;
        endif
    
        :Pre-Game Screen;
    
        repeat
            if (Assignment) then
                :Assignment Setup;
                :Assignment Battle;
                :Receive Rewards;
                :Change Spells;
            elseif (Exam) then
                :Exam Setup;
                :Exam Battles;
                :Receive Rewards;
                :Change Spells;
            elseif (Final) then
                :Final Battles;
                :Receive Rewards;
                :Change Spells;
            elseif (Library/Lecture) then
                :Tutorials;
            elseif (Exit) then
                stop
            endif

Suggested Project Timeline
==========================

Additional Ideas and Possibilities
==================================

