from panda3d.core import *


MAP_SIZE = 32
SEL_NONE = 0
SEL_CURS = 1 << 0
SEL_MOVE = 1 << 1


class Terrain:
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

	def update_selection(self):
		self.selection_texture.load(self.selection_image)