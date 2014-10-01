import math
import random
import json

from panda3d.core import *

from .terrain import Terrain
from stance_generator import StanceGenerator, Stance
from stats import *


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


class _PlayerEncoder(json.JSONEncoder):
	ATTRIBS = [
		"level",
		"remaining_movement",
		"health",
		"name",
		"atb",
		"movement",
		"range",
		"damage",
		"defense",
		"regen",
		"speed",
	]

	def default(self, obj):
		if isinstance(obj, Player):
			return {i: getattr(obj, i) for i in self.ATTRIBS}
		return json.JSONEncoder.default(self, obj)


class Player(object):
	@classmethod
	def from_player_chassis(cls, name, level=1):
		player = Player(level=level)
		player.load_player_chassis(name)
		player.model.setColor(0.961, 0.725, 0.012, 1.0)
		return player

	def __init__(self, name='', level=1):
		self.level = level
		self.remaining_movement = 0
		self.health = 1

		self._stat_vector = [0.0 for i in range(6)]
		self.stances = []
		self.active_stance = None

		self.load_player_chassis("default_player")
		self.stances = StanceGenerator.n_random(3)

		self.name = name

		self.target = None

		self.action_set = ["MOVE", "ATTACK"]

		self.atb = 0

		self._grid_pos = [0, 0, 0]

		self.model = base.loader.loadModel("player")
		self.model.setColor(0.510, 0.0, 0.255)
		self.model.reparentTo(base.render)

		self.grid_position = [16, 16, 0]

		self._credit_vector = [1.0/6.0 for i in range(6)]

	def __del__(self):
		self.model.removeNode()

	def to_json(self):
		return _PlayerEncoder().encode(self)

	def roll_initiative(self):
		self.atb = random.random() * self.speed

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
		self._stat_vector = load_vector(name, data["stat_vector"])

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

		retval = self.level * self._stat_vector[stat_index]

		if self.active_stance is not None:
			retval += getattr(self.active_stance, attrib)

		if retval < 0:
			retval = 0

		retval *= STAT_SCALE[stat_index]
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
		return self.__get_stance_attrib("speed")

	@property
	def grid_position(self):
		return self._grid_pos

	@grid_position.setter
	def grid_position(self, value):
		self._grid_pos = value
		self.model.setPos(*Terrain.grid_to_world(*value))