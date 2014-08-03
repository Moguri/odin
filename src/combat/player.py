import random

from panda3d.core import *

from .terrain import Terrain


class Player(object):
	def __init__(self, name=''):
		self.movement = 3
		self.range = 5
		self.damage = 1
		self.health = 1
		self.speed = 2

		self.name = name

		self.target = None

		self.action_set = ["MOVE", "ATTACK"]

		self.atb = 0

		self._grid_pos = [0, 0, 0]
		self.model = base.loader.loadModel("player")
		self.model.reparentTo(base.render)

		self.grid_position = [16, 16, 0]

	def __del__(self):
		self.model.removeNode()

	def roll_intiative(self):
		self.atb = random.randint(0, self.speed)

	@property
	def grid_position(self):
		return self._grid_pos

	@grid_position.setter
	def grid_position(self, value):
		self._grid_pos = value
		self.model.setPos(*Terrain.grid_to_world(*value))