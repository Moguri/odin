import random

from panda3d.core import *


MAP_SIZE = 32
CELL_SIZE = 1
SEL_NONE = 0
SEL_CURS = 1 << 0
SEL_MOVE = 1 << 1
SEL_ATTK = 1 << 2


class Terrain(object):
	# UNTESTED
	# @classmethod
	# def world_to_grid(cls, x, y, z):
	# 	position = [x, y, z]
	# 	half_size = MAP_SIZE / 2
	# 	position[0] = int(position[0] * half_size + half_size) / CELL_SIZE
	# 	position[1] = int(position[1] * half_size + half_size) / CELL_SIZE
	#
	# 	return position

	@classmethod
	def grid_to_world(cls, x, y, z):
		position = [x, y, z]
		position[0] = position[0] - MAP_SIZE/2 + CELL_SIZE / 2.0
		position[1] = position[1] - MAP_SIZE/2 + CELL_SIZE / 2.0

		return position

	@classmethod
	def get_random_tile(cls):
		x = random.randint(0, MAP_SIZE-1)
		y = random.randint(0, MAP_SIZE-1)
		return [x, y, 0]

	def __init__(self):
		# Load the environment model.
		self.model = base.loader.loadModel("terrain")
		# Reparent the model to render.
		self.model.reparentTo(base.render)

		# Load and set terrain shader
		terrain_shader = Shader.load(Shader.SLGLSL, "shaders/basic.vs", "shaders/terrain.fs", "")
		self.model.setShader(terrain_shader)

		# Setup selection map
		self.selection_texture = Texture()
		self.selection_texture.set_compression(Texture.CMOff)
		self.selection_texture.set_component_type(Texture.TUnsignedByte)
		self.selection_texture.set_format(Texture.FRed)
		self.model.setShaderInput("selection_map", self.selection_texture)

		# Setup selection data
		self.selection_image = PNMImage(MAP_SIZE, MAP_SIZE, 1)

	def clear_selection(self):
		self.selection_image.fill(SEL_NONE)

	def set_cursor_selection(self, x, y):
		self.selection_image.setXelVal(x, y, SEL_CURS)

	def _display_range(self, center, radius, value):
		for y in range(center[1]-radius, center[1]+radius+1):
			for x in range(center[0]-radius, center[0]+radius+1):
				if x < 0 or x >= MAP_SIZE or y < 0 or y >= MAP_SIZE:
					continue

				distance = abs(x-center[0]) + abs(y-center[1])
				if distance <= radius:
					old = self.selection_image.getGrayVal(x, y)
					self.selection_image.setXelVal(x, y, old+value)

	def display_move_range(self, player):
		center = player.grid_position
		radius = player.movement
		self._display_range(center, radius, SEL_MOVE)

	def display_attack_range(self, player):
		center = player.grid_position
		radius = player.range
		self._display_range(center, radius, SEL_ATTK)

	def update_selection(self):
		self.selection_texture.load(self.selection_image)