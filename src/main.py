import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

from direct.showbase.ShowBase import ShowBase

from panda3d.core import *

from combat.terrain import Terrain as CombatTerrain, MAP_SIZE
from combat.player import Player as CombatPlayer


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("escape", sys.exit)
		self.accept("arrow_up", self.sel_up)
		self.accept("arrow_left", self.sel_left)
		self.accept("arrow_down", self.sel_down)
		self.accept("arrow_right", self.sel_right)
		self.accept("arrow_up-repeat", self.sel_up)
		self.accept("arrow_left-repeat", self.sel_left)
		self.accept("arrow_down-repeat", self.sel_down)
		self.accept("arrow_right-repeat", self.sel_right)
		self.accept("enter", self.accept_selection)
		self.accept("1", self.enter_move_mode)
		self.accept("2", self.enter_attack_mode)

		self.terrain = CombatTerrain()
		self.player = CombatPlayer()

		self.disableMouse()
		self.camera.setPos(7, -7, 10)
		self.camera.setHpr(45, -45, 0)
		self.camLens.setFov(65)

		self.taskMgr.add(self.main_loop, "MainLoop")

		self.selected_pos = [16, 16, 0]

		self.mode = "NONE"

	def accept_selection(self):
		if self.mode == "MOVE":
			x = (self.selected_pos[0]-self.player.grid_position[0])
			y = (self.selected_pos[1]-self.player.grid_position[1])
			distance = x**2 + y**2
			if distance <= self.player.movement**2:
				self.player.grid_position = self.selected_pos[:]

	def enter_move_mode(self):
		self.mode = "MOVE" if self.mode != "MOVE" else "NONE"

	def enter_attack_mode(self):
		self.mode = "ATTACK" if self.mode != "ATTACK" else "NONE"

	def sel_up(self):
		self.selected_pos[0] -= 1

	def sel_left(self):
		self.selected_pos[1] -= 1

	def sel_down(self):
		self.selected_pos[0] += 1

	def sel_right(self):
		self.selected_pos[1] += 1

	def main_loop(self, task):
		# Bound selection
		self.selected_pos[0] = min(max(self.selected_pos[0], 0), MAP_SIZE-1)
		self.selected_pos[1] = min(max(self.selected_pos[1], 0), MAP_SIZE-1)

		self.terrain.clear_selection()
		self.terrain.set_cursor_selection(*self.selected_pos[:2])
		if self.mode == "MOVE":
			self.terrain.display_move_range(self.player)
		if self.mode == "ATTACK":
			self.terrain.display_attack_range(self.player)
		self.terrain.update_selection()
		return task.cont

app = Game()
app.run()