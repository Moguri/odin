
import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

# This import should be kept near the top to avoid issues with CEF/Chromium hooking malloc
from cefexample import CEFPanda


from direct.showbase.ShowBase import ShowBase

from panda3d.core import *

from combat.terrain import Terrain as CombatTerrain, MAP_SIZE
from combat.player import Player as CombatPlayer


loadPrcFileData("", "textures-power-2 none")


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("f1", sys.exit)
		self.accept("arrow_up", self.sel_up)
		self.accept("arrow_left", self.sel_left)
		self.accept("arrow_down", self.sel_down)
		self.accept("arrow_right", self.sel_right)
		self.accept("arrow_up-repeat", self.sel_up)
		self.accept("arrow_left-repeat", self.sel_left)
		self.accept("arrow_down-repeat", self.sel_down)
		self.accept("arrow_right-repeat", self.sel_right)
		self.accept("enter", self.accept_selection)
		self.accept("escape", self.escape)
		self.accept("1", self.enter_move_mode)
		self.accept("2", self.enter_attack_mode)
		self.accept("3", self.end_turn)

		self.win.setCloseRequestEvent("f1")

		self.ui = CEFPanda()
		# self.accept("space", self.ui.execute_js, ["setActiveSelection(1)"])

		self.terrain = CombatTerrain()
		self.player = CombatPlayer("Player")
		self.player.roll_intiative()

		self.enemies = []
		self.active_set = []

		self.disableMouse()
		self.camera.setPos(25, -25, 28)
		self.camera.setHpr(45, -45, 0)
		self.camLens.setFov(65)

		self.taskMgr.add(self.main_loop, "MainLoop")

		self.ui_selection = 0

		self.selected_pos = [16, 16, 0]

		self.mode = "NONE"

	def escape(self):
		self.mode = "NONE"

	def accept_selection(self):
		p0 = self.player.grid_position
		p1 = self.selected_pos
		if self.mode == "MOVE":
			if CombatTerrain.check_distance(self.player.movement, p0, p1):
				self.player.grid_position = self.selected_pos[:]
				self.player.action_set.remove("MOVE")
				self.mode = "NONE"
		elif self.mode == "ATTACK":
			if CombatTerrain.check_distance(self.player.range, p0, p1):
				for enemy in self.enemies:
					if enemy.grid_position == self.selected_pos:
						enemy.health -= self.player.damage
						self.player.action_set.remove("ATTACK")
						self.mode = "NONE"
		else:
			if self.ui_selection == 0:
				self.enter_move_mode()
			elif self.ui_selection == 1:
				self.enter_attack_mode()
			elif self.ui_selection == 2:
				self.end_turn()

	def enter_move_mode(self):
		if "MOVE" in self.player.action_set:
			self.mode = "MOVE" if self.mode != "MOVE" else "NONE"

	def enter_attack_mode(self):
		if "ATTACK" in self.player.action_set:
			self.mode = "ATTACK" if self.mode != "ATTACK" else "NONE"

	def end_turn(self):
		print("clearing action set")
		self.player.action_set = []
		self.ui_selection = 0

	def sel_up(self):
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[1] += 1
		else:
			self.ui_selection -= 1

	def sel_left(self):
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[0] -= 1

	def sel_down(self):
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[1] -= 1
		else:
			self.ui_selection += 1

	def sel_right(self):
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[0] += 1

	def main_loop(self, task):
		# Bound selection
		self.selected_pos[0] = min(max(self.selected_pos[0], 0), MAP_SIZE-1)
		self.selected_pos[1] = min(max(self.selected_pos[1], 0), MAP_SIZE-1)

		# Track remaining enemies and add new ones if none are left
		for dead_enemy in [e for e in self.enemies if e.health <= 0]:
			if dead_enemy in self.active_set:
				self.active_set.remove(dead_enemy)
		self.enemies = [e for e in self.enemies if e.health > 0]
		if not self.enemies or self.player.health <= 0:
			self.player = CombatPlayer("Player")
			self.player.roll_intiative()

			self.enemies = []
			for i in range(3):
				enemy = CombatPlayer(i)
				enemy.grid_position = CombatTerrain.get_random_tile()
				enemy.roll_intiative()
				enemy.target = self.player
				self.enemies.append(enemy)

			self.active_set = []

		# Get current participants
		participants = [self.player] + self.enemies
		if not self.active_set:
			while not self.active_set:
				for participant in participants:
					participant.atb += participant.speed
					if participant.atb >= 10:
						self.active_set.append(participant)

			self.active_set.sort(key=lambda x: x.atb)
			for participant in self.active_set:
				participant.action_set = ["ATTACK", "MOVE"]

		current_player = self.active_set[0]
		if current_player != self.player and current_player.target:
			center = current_player.grid_position
			radius = current_player.movement
			target = current_player.target.grid_position
			closest = CombatTerrain.find_closest_in_range(center, radius, target)
			if closest:
				current_player.grid_position = closest
			center = current_player.grid_position
			if CombatTerrain.check_distance(current_player.range, center, target):
				current_player.target.health -= current_player.damage
			current_player.action_set = []

		if not current_player.action_set:
			print("%s has finished their turn" % current_player.name)
			current_player.atb -= 10
			self.active_set.remove(current_player)

		# Handle selection
		self.terrain.clear_selection()
		self.terrain.set_cursor_selection(*self.selected_pos[:2])
		if self.mode == "MOVE":
			self.terrain.display_move_range(self.player)
		if self.mode == "ATTACK":
			self.terrain.display_attack_range(self.player)
		self.terrain.update_selection()


		if self.ui_selection > 2:
			self.ui_selection = 0
		elif self.ui_selection < 0:
			self.ui_selection = 2
		self.ui.execute_js("setActiveSelection(%d)" % self.ui_selection)
		return task.cont

app = Game()
app.run()