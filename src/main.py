import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase

from panda3d.core import *


class MyApp(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.accept("w", self.sel_up)
		self.accept("a", self.sel_left)
		self.accept("s", self.sel_down)
		self.accept("d", self.sel_right)

		# Load the environment model.
		self.environ = self.loader.loadModel("terrain")
		# Reparent the model to render.
		self.environ.reparentTo(self.render)

		# Load and set terrain shader
		terrain_shader = Shader.load(Shader.SLGLSL, "shaders/basic.vs", "shaders/terrain.fs", "")
		self.environ.setShader(terrain_shader)

		# Load a dummy player
		self.player_model = self.loader.loadModel("player")
		self.player_model.setPos(0.5, 0.5, 0)
		self.player_model.reparentTo(self.render)

		# Setup selection map
		self.selection_texture = Texture()
		self.selection_texture.set_compression(Texture.CMOff)
		self.selection_texture.set_component_type(Texture.TUnsignedByte)
		self.selection_texture.set_format(Texture.FRed)
		self.environ.setShaderInput("selection_map", self.selection_texture)

		self.disableMouse()
		self.camera.setPos(7, -7, 10)
		self.camera.setHpr(45, -45, 0)
		self.camLens.setFov(65)

		self.taskMgr.add(self.update_selection, "UpdateSelection")

		self.selected_pos = [16, 16]

	def sel_up(self):
		self.selected_pos[0] -= 1

	def sel_left(self):
		self.selected_pos[1] -= 1

	def sel_down(self):
		self.selected_pos[0] += 1

	def sel_right(self):
		self.selected_pos[1] += 1

	def update_selection(self, task):
		image = PNMImage(32, 32, 1)
		image.fill(0)

		val = 1 << 1
		center = 16, 16
		radius = 1

		for y in range(center[1]-radius, center[1]+radius+1):
			for x in range(center[0]-radius, center[1]+radius+1):
				image.setXelVal(x, y, val)

		val = image.getGrayVal(self.selected_pos[0], self.selected_pos[1])
		image.setXelVal(self.selected_pos[0], self.selected_pos[1], val+1)

		self.selection_texture.load(image)

		return task.cont

app = MyApp()
app.run()