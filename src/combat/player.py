from panda3d.core import *

from .terrain import Terrain


class Player(object):
	def __init__(self):
		self.movement = 3
		self.range = 5

		self._grid_pos = [0, 0, 0]
		self.model = base.loader.loadModel("player")
		self.model.reparentTo(base.render)

		self.grid_position = [16, 16, 0]


	@property
	def grid_position(self):
		return self._grid_pos

	@grid_position.setter
	def grid_position(self, value):
		self._grid_pos = value
		self.model.setPos(*Terrain.grid_to_world(*value))