import random

from panda3d.core import *

from .terrain import Terrain


class Stance(object):
	def __init__(self):
		self.movement = 0
		self.range = 0
		self.damage = 0
		self.speed = 0


class Player(object):
	def __init__(self, name=''):
		self._movement = 3
		self.remaining_movement = 0
		self._range = 5
		self._damage = 1
		self.health = 1
		self._speed = 2

		self.name = name

		self.target = None

		self.action_set = ["MOVE", "ATTACK"]

		self.atb = 0

		self._grid_pos = [0, 0, 0]
		self.model = base.loader.loadModel("player")
		self.model.reparentTo(base.render)

		self.grid_position = [16, 16, 0]

		temp_stance = Stance()
		temp_stance.range = 5
		self.stances = [temp_stance]
		self.active_stance = self.stances[0]

	def __del__(self):
		self.model.removeNode()

	def roll_intiative(self):
		self.atb = random.randint(0, self.speed)

	def __get_stance_attrib(self, attrib):
		retval = getattr(self, "_" + attrib)

		if self.active_stance is not None:
			retval += getattr(self.active_stance, attrib)

		if retval < 0:
			retval = 0
		return retval
		
	@property
	def movement(self):
		return self.__get_stance_attrib("movement")

	@property
	def range(self):
		return self.__get_stance_attrib("range")

	@property
	def damage(self):
		return self.__get_stance_attrib("damage")

	@property
	def speed(self):
		return self.__get_stance_attrib("speed")

	@property
	def grid_position(self):
		return self._grid_pos

	@grid_position.setter
	def grid_position(self, value):
		self._grid_pos = value
		self.model.setPos(*Terrain.grid_to_world(*value))