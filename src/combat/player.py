import math
import random
import json

from panda3d.core import *

from .terrain import Terrain


STAT_MOVEMENT, STAT_RANGE, STAT_DAMAGE, STAT_DEFENSE, STAT_REGEN, STAT_SPEED = range(6)
STAT_SCALE = [10.0, 10.0, 2.0, 2.0, 0.0, 4.0]


class Stance(object):
	def __init__(self):
		self.name = "Stance"
		self.movement = 0
		self.range = 0
		self.damage = 0
		self.speed = 0


class Player(object):
	@classmethod
	def from_player_chassis(cls, name):
		path = "data/pc_%s.json" % name
		with open(path) as fin:
			data = json.load(fin)

		if "name" in data:
			pretty_name = data["name"]
		else:
			pretty_name = " ".join([i.title() for i in name.split("_")])

		player = Player(pretty_name)
		player.model.setColor(0.961, 0.725, 0.012, 1.0)

		stat_vector = [float(i) for i in data["stat_vector"]]
		if len(stat_vector) != 6:
			print("Incorrectly sized stat vector for player chassis: %s" % name)
			return player

		norm = sum(stat_vector)
		if norm == 0:
			print("Zero stat vector for player chassis: %s" % name)
			return player

		for i, value in enumerate(stat_vector):
			stat_vector[i] = value / norm * STAT_SCALE[i]

		player._movement = stat_vector[STAT_MOVEMENT]
		player._range = stat_vector[STAT_RANGE]
		player._damage = stat_vector[STAT_DAMAGE]
		# TODO: Add defense
		# TODO: Add regen
		player._speed = stat_vector[STAT_SPEED]

		return player

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
		self.model.setColor(0.510, 0.0, 0.255)
		self.model.reparentTo(base.render)

		self.grid_position = [16, 16, 0]

		temp_stance = Stance()
		temp_stance.range = 5
		self.stances = [temp_stance]
		self.active_stance = None

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

	def __get_stance_attribi(self, attrib):
		return int(math.floor(self.__get_stance_attrib(attrib)))

	@property
	def movement(self):
		return self.__get_stance_attribi("movement")

	@property
	def range(self):
		return self.__get_stance_attribi("range")

	@property
	def damage(self):
		return self.__get_stance_attrib("damage")

	@property
	def speed(self):
		return self.__get_stance_attribi("speed")

	@property
	def grid_position(self):
		return self._grid_pos

	@grid_position.setter
	def grid_position(self, value):
		self._grid_pos = value
		self.model.setPos(*Terrain.grid_to_world(*value))