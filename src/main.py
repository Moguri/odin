import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase

from panda3d.core import *

from combat.terrain import Terrain as CombatTerrain


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.accept("w", self.sel_up)
		self.accept("a", self.sel_left)
		self.accept("s", self.sel_down)
		self.accept("d", self.sel_right)

		self.terrain = CombatTerrain()

		# Load a dummy player
		self.player_model = self.loader.loadModel("player")
		self.player_model.setPos(0.5, 0.5, 0)
		self.player_model.reparentTo(self.render)

		self.disableMouse()
		self.camera.setPos(7, -7, 10)
		self.camera.setHpr(45, -45, 0)
		self.camLens.setFov(65)

		self.taskMgr.add(self.main_loop, "MainLoop")

		self.selected_pos = [16, 16]

	def sel_up(self):
		self.selected_pos[0] -= 1

	def sel_left(self):
		self.selected_pos[1] -= 1

	def sel_down(self):
		self.selected_pos[0] += 1

	def sel_right(self):
		self.selected_pos[1] += 1

	def main_loop(self, task):
		self.terrain.clear_selection()
		self.terrain.set_cursor_selection(*self.selected_pos)
		self.terrain.update_selection()
		return task.cont

app = Game()
app.run()