
import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

# This import should be kept near the top to avoid issues with CEF/Chromium hooking malloc
from cefexample import CEFPanda


from direct.showbase.ShowBase import ShowBase, DirectObject
from direct.interval.LerpInterval import LerpPosInterval

from panda3d.core import *

from combat.terrain import Terrain as CombatTerrain, MAP_SIZE
from combat.player import Player as CombatPlayer
from stance_generator import StanceGenerator


loadPrcFileData("", "textures-power-2 none")


class CombatState(DirectObject.DirectObject):
	def __init__(self):
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

		base.ui.load('ui.html')

		def stm():
			base.ui.execute_js("switchToMenu('stances')")
		self.accept("space", stm)

		self.terrain = CombatTerrain()
		self.player = CombatPlayer("Player")
		self.player.roll_initiative()

		self.enemies = []
		self.active_set = []

		base.disableMouse()
		base.camera.setPos(25, -25, 28)
		base.camera.setHpr(45, -45, 0)
		base.camLens.setFov(65)

		self.ui_last = self.ui_selection = 0
		base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection, True)

		self.selected_pos = [16, 16, 0]

		self.mode = "NONE"

		# Setup the combatants
		self.player = CombatPlayer("Player", level=3)
		for stance in self.player.stances:
			print(stance)
		stance_str = "[" + ",".join(["'%s'" % i.name for i in self.player.stances]) + "]"
		base.ui.execute_js("setStances(%s)" % stance_str, onload=True)
		self.player.roll_initiative()

		self.enemies = []
		for i in range(3):
			enemy = CombatPlayer.from_player_chassis("clay_golem")
			enemy.grid_position = CombatTerrain.get_random_tile()
			enemy.roll_initiative()
			enemy.target = self.player
			self.enemies.append(enemy)

		self.active_set = []
		self.move_interval = None

	def destroy(self):
		self.ignoreAll()
		for n in base.render.getChildren():
			n.removeNode()

	def escape(self):
		if self.mode == "STANCE":
			self.ui_selection = 0
			base.ui.execute_js("switchToMenu('actions')")
		self.mode = "NONE"

	def accept_selection(self):
		p0 = self.player.grid_position
		p1 = self.selected_pos
		if self.mode == "MOVE":
			distance = CombatTerrain.get_distance(p0, p1)
			if distance <= self.player.remaining_movement:
				start_pos = self.player.model.getPos()
				self.player.grid_position = self.selected_pos[:]
				self.player.remaining_movement -= distance
				if self.player.remaining_movement <= 0:
					self.player.action_set.remove("MOVE")
					base.ui.execute_js("disableItem('MOVE')")
				end_pos = self.player.model.getPos()
				self.move_interval = self.player.model.posInterval(distance * 0.125, end_pos, start_pos, blendType='easeInOut')
				self.move_interval.start()
				self.mode = "ANIMATION"
		elif self.mode == "ATTACK":
			if CombatTerrain.check_distance(self.player.range, p0, p1):
				for enemy in self.enemies:
					if enemy.grid_position == self.selected_pos:
						enemy.health -= self.player.damage
						self.player.action_set.remove("ATTACK")
						base.ui.execute_js("disableItem('ATTACK')")
						self.mode = "NONE"
		elif self.mode == "STANCE":
			self.player.active_stance = self.player.stances[self.ui_selection]
			self.player.action_set.remove("STANCE")
			base.ui.execute_js("disableItem('STANCE')")
			self.escape()
		else:
			if self.ui_selection == 0:
				self.enter_stance_mode()
			elif self.ui_selection == 1:
				self.enter_move_mode()
			elif self.ui_selection == 2:
				self.enter_attack_mode()
			elif self.ui_selection == 3:
				self.end_turn()

	def enter_stance_mode(self):
		if "STANCE" in self.player.action_set:
			self.mode = "STANCE"
			base.ui.execute_js("switchToMenu('stances')")

	def enter_move_mode(self):
		if "MOVE" in self.player.action_set:
			self.mode = "MOVE" if self.mode != "MOVE" else "NONE"

	def enter_attack_mode(self):
		if "ATTACK" in self.player.action_set:
			self.mode = "ATTACK" if self.mode != "ATTACK" else "NONE"

	def end_turn(self):
		self.player.action_set = []
		self.ui_selection = 0
		self.mode = "NONE"

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

	def main_loop(self):
		# Reset anim mode
		if self.move_interval is not None and self.move_interval.isStopped():
			self.move_interval = None
			self.mode = "NONE"
		if self.mode == "ANIMATION":
			return

		# Bound selection
		self.selected_pos[0] = min(max(self.selected_pos[0], 0), MAP_SIZE-1)
		self.selected_pos[1] = min(max(self.selected_pos[1], 0), MAP_SIZE-1)

		# Track remaining enemies and and exit if none are left
		for dead_enemy in [e for e in self.enemies if e.health <= 0]:
			if dead_enemy in self.active_set:
				self.active_set.remove(dead_enemy)
		self.enemies = [e for e in self.enemies if e.health > 0]
		if not self.enemies or self.player.health <= 0:
			new_pool = StanceGenerator.n_from_pool(5, self.player.stances)
			for stance in new_pool:
				print(stance)
			base.change_state(LobbyState)
			return

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
				participant.action_set = ["ATTACK", "MOVE", "STANCE"]
				participant.remaining_movement = participant.movement
				for i in participant.action_set:
					base.ui.execute_js("enableItem('%s')" % i)

		current_player = self.active_set[0]
		if current_player != self.player and current_player.target:
			target = current_player.target.grid_position
			if "MOVE" in current_player.action_set:
				center = current_player.grid_position
				radius = current_player.movement
				closest = CombatTerrain.find_closest_in_range(center, radius, target)
				if closest:
					distance = CombatTerrain.get_distance(center, closest)
					start_pos = current_player.model.getPos()
					current_player.grid_position = closest
					end_pos = current_player.model.getPos()
					self.move_interval = current_player.model.posInterval(distance * 0.125, end_pos, start_pos, blendType='easeInOut')
					self.move_interval.start()
				current_player.action_set.remove("MOVE")
				self.mode = "ANIMATION"
			elif "ATTACK" in current_player.action_set:
				center = current_player.grid_position
				if CombatTerrain.check_distance(current_player.range, center, target):
					current_player.target.health -= current_player.damage
				current_player.action_set.remove("ATTACK")
			elif "STANCE" in current_player.action_set:
				current_player.active_stance = current_player.stances[0] if current_player.stances else None
				current_player.action_set.remove("STANCE")
			else:
				current_player.action_set = []

		if not current_player.action_set:
			current_player.atb -= 10
			self.active_set.remove(current_player)

		# Handle selection
		self.terrain.clear_selection()
		self.terrain.set_cursor_selection(*self.selected_pos[:2])
		if self.mode == "MOVE":
			self.terrain.display_move_range(self.player)
		if self.mode == "ATTACK":
			self.terrain.display_attack_range(self.player)
		if self.mode == "NONE":
			self.selected_pos = self.player.grid_position[:]
		self.terrain.update_selection()

		if self.mode == "STANCE":
			ui_max = len(self.player.stances) - 1
		else:
			ui_max = 3

		if self.ui_selection > ui_max:
			self.ui_selection = 0
		elif self.ui_selection < 0:
			self.ui_selection = ui_max

		if self.ui_last != self.ui_selection:
			base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection)
			self.ui_last = self.ui_selection


class LobbyState(DirectObject.DirectObject):
	def __init__(self):
		self.accept("arrow_up", self.sel_up)
		self.accept("arrow_left", self.sel_up)
		self.accept("arrow_down", self.sel_down)
		self.accept("arrow_right", self.sel_down)
		self.accept("arrow_up-repeat", self.sel_up)
		self.accept("arrow_left-repeat", self.sel_up)
		self.accept("arrow_down-repeat", self.sel_down)
		self.accept("arrow_right-repeat", self.sel_down)
		self.accept("enter", self.accept_selection)
		self.accept("escape", self.escape)

		base.ui.load('lobby_ui.html')

		self.ui_last = self.ui_selection = 0
		self.ui_options = [
			"STUDENT_INFO",
			"COURSEWORK",
			"OPTIONS",
			"QUIT",
		]
		self.mode = None
		base.ui.execute_js("setActiveTab(%d)" % self.ui_selection, True)

	def destroy(self):
		self.ignoreAll()

	def accept_selection(self):
		if self.mode is None:
			self.mode = self.ui_options[self.ui_selection]
			self.ui_selection = 0
	
			if self.mode == "STUDENT_INFO":
				pass
			elif self.mode == "COURSEWORK":
				base.change_state(CombatState)
			elif self.mode == "OPTIONS":
				pass
			elif self.mode == "QUIT":
				sys.exit()

	def escape(self):
		if self.mode is not None:
			self.ui_selection = self.ui_options.index(self.mode)
			self.mode = None

	def sel_up(self):
		self.ui_selection -= 1

	def sel_down(self):
		self.ui_selection += 1

	def main_loop(self):

		ui_max = 3
		if self.ui_selection > ui_max:
			self.ui_selection = 0
		elif self.ui_selection < 0:
			self.ui_selection = ui_max

		if self.ui_last != self.ui_selection:
			if self.mode is None:
				base.ui.execute_js("setActiveTab(%d)" % self.ui_selection)
			self.ui_last = self.ui_selection


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("f1", sys.exit)
		self.win.setCloseRequestEvent("f1")

		self.ui = CEFPanda()

		self.state = LobbyState()

		self.taskMgr.add(self.main_loop, "MainLoop")

	def change_state(self, new_state):
		self.state.destroy()
		self.state = new_state()

	def main_loop(self, task):
		self.state.main_loop()
		return task.cont


app = Game()
app.run()