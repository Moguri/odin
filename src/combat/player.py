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
		self.level = 1
		self.cost_factor = 0.0
		self.benefit_vector = [0.0 for i in range(6)]
		self.cost_vector = [0.0 for i in range(6)]

	def _calculate_effect(self, stat_index):
		cost_factor = self.level * self.cost_factor
		benefit_factor = self.level + self.level * self.cost_factor
		benefit = self.benefit_vector[stat_index]
		cost = self.cost_vector[stat_index]

		factor = benefit_factor * benefit - cost_factor * cost

		return factor

	@property
	def movement(self):
		return self._calculate_effect(STAT_MOVEMENT)

	@property
	def range(self):
		return self._calculate_effect(STAT_RANGE)

	@property
	def damage(self):
		return self._calculate_effect(STAT_DAMAGE)

	@property
	def defense(self):
		return self._calculate_effect(STAT_DEFENSE)

	@property
	def regen(self):
		return self._calculate_effect(STAT_REGEN)

	@property
	def speed(self):
		return self._calculate_effect(STAT_SPEED)


def load_vector(name, vector_dict):
	default = [1.0/6.0 for i in range(6)]

	vector = [float(i) for i in vector_dict]
	if len(vector) != 6:
		print("Incorrectly sized vector for player chassis: %s" % name)
		return default

	norm = sum(vector)
	if norm == 0:
		print("Zero vector for player chassis: %s" % name)
		return default

	for i, value in enumerate(vector):
		vector[i] = value / norm

	return vector


def load_stance(name, stance_dict):
	stance = Stance()
	stance.name = stance_dict.get("name", "Stance")
	stance.cost_factor = stance_dict.get("cost_factor", 0.0)

	default_vector = [1.0 for i in range(6)]
	stance.benefit_vector = load_vector(name, stance_dict.get("benefits", default_vector))
	stance.cost_vector = load_vector(name, stance_dict.get("costs", default_vector))

	return stance


class Player(object):
	@classmethod
	def from_player_chassis(cls, name, level=1):
		player = Player(level=level)
		player.load_player_chassis(name)
		player.model.setColor(0.961, 0.725, 0.012, 1.0)
		return player

	def __init__(self, name='', level=1):
		self.level = level
		self._movement = 3
		self.remaining_movement = 0
		self._range = 5
		self._damage = 1
		self.health = 1
		self._defense = 0
		self._regen = 0
		self._speed = 2

		self.load_player_chassis("default_player")

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
		temp_stance.benefit_vector[STAT_RANGE] = 1
		self.stances = [temp_stance]
		self.active_stance = None

		self._credit_vector = [1.0/6.0 for i in range(6)]

	def __del__(self):
		self.model.removeNode()

	def roll_initiative(self):
		self.atb = random.randint(0, self.speed)

	def load_player_chassis(self, name):
		path = "data/pc_%s.json" % name
		with open(path) as fin:
			data = json.load(fin)

		if "name" in data:
			pretty_name = data["name"]
		else:
			pretty_name = " ".join([i.title() for i in name.split("_")])
		self.name = pretty_name

		if "stat_vector" not in data:
			print("No stat_vector in player chassis: %s" % name)
			return
		stat_vector = load_vector(name, data["stat_vector"])

		self._movement = stat_vector[STAT_MOVEMENT]
		self._range = stat_vector[STAT_RANGE]
		self._damage = stat_vector[STAT_DAMAGE]
		self._defense = stat_vector[STAT_DEFENSE]
		self._regen = stat_vector[STAT_REGEN]
		self._speed = stat_vector[STAT_SPEED]

		if "credit_vector" not in data:
			print("No credit_vector in player chassis: %s" % name)
			return
		self._credit_vector = load_vector(name, data["credit_vector"])

		stances = []
		if "stances" in data:
			for stance in data["stances"]:
				stances.append(load_stance(name, stance))
			self.stances = stances

	def __get_stance_attrib(self, attrib):
		stat_index = eval("STAT_"+attrib.upper())

		retval = self.level * getattr(self, "_" + attrib)

		if self.active_stance is not None:
			retval += getattr(self.active_stance, attrib)

		if retval < 0:
			retval = 0

		retval *= STAT_SCALE[stat_index]
		print(self.name, attrib, retval)
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
	def defense(self):
		return self.__get_stance_attrib("defense")

	@property
	def regen(self):
		return self.__get_stance_attrib("regen")

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