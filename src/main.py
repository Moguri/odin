
import sys

import os
os.environ['PANDA_PRC_DIR'] = os.path.join(os.path.dirname(__file__), 'etc')

# This import should be kept near the top to avoid issues with CEF/Chromium hooking malloc
from cefpanda import CEFPanda


from direct.showbase.ShowBase import ShowBase, DirectObject
from direct.interval.LerpInterval import LerpPosInterval

from panda3d.core import *

from combat.terrain import Terrain as CombatTerrain, MAP_SIZE
from combat.player import Player as CombatPlayer
from stance_generator import StanceGenerator, stances_to_json


class GameState(object, DirectObject.DirectObject):
	def __init__(self, _base, ui=None):
		DirectObject.DirectObject.__init__(self)
		self.base = _base

		if self.base.player is None:
			print("Creating default player")
			self.base.player = CombatPlayer("Player", level=3)
		self.player = self.base.player

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

		# Load UI
		if ui is not None:
			self.base.ui.load('ui/' + ui + '.html')

		self.ui_last = self.ui_selection = 0

		# Load UI sounds
		self.base.sfxManagerList[0].setVolume(0.5)  # TODO: Make this user settable
		self.uifx_selection = self.base.loader.loadSfx("audio/MENU_Pick.wav")
		self.uifx_accept = self.base.loader.loadSfx("audio/MENU B_Select.wav")
		self.uifx_back = self.base.loader.loadSfx("audio/MENU B_Back.wav")

	def destroy(self):
		self.ignoreAll()

	def accept_selection(self):
		self.uifx_accept.play()

	def escape(self):
		self.uifx_back.play()

	def sel_up(self):
		self.uifx_selection.play()
		self.ui_selection -= 1

	def sel_down(self):
		self.uifx_selection.play()
		self.ui_selection += 1

	def sel_left(self):
		self.uifx_selection.play()
		self.sel_up()

	def sel_right(self):
		self.uifx_selection.play()
		self.sel_down()

	def main_loop(self):
		pass


class CombatState(GameState):
	def __init__(self, _base):
		super(CombatState, self).__init__(_base, 'combat_ui')
		self.accept("1", self.enter_move_mode)
		self.accept("2", self.enter_attack_mode)
		self.accept("3", self.end_turn)

		self.terrain = CombatTerrain()
		self.player = CombatPlayer("Player")
		self.player.roll_initiative()

		self.enemies = []
		self.active_set = []

		self.base.disableMouse()
		self.base.camera.setPos(25, -25, 28)
		self.base.camera.setHpr(45, -45, 0)
		self.base.camLens.setFov(65)

		self.base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection, True)

		self.selected_pos = [16, 16, 0]

		self.mode = "NONE"

		# Setup the combatants
		stance_str = "[" + ",".join(["'%s'" % i.name for i in self.player.stances]) + "]"
		self.base.ui.execute_js("setStances(%s)" % stance_str, onload=True)
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
		super(CombatState, self).destroy()
		for n in self.base.render.getChildren():
			n.removeNode()

	def escape(self):
		super(CombatState, self).escape()
		if self.mode == "STANCE":
			self.ui_selection = 0
			self.base.ui.execute_js("switchToMenu('actions')")
		self.mode = "NONE"

	def accept_selection(self):
		super(CombatState, self).accept_selection()
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
					self.base.ui.execute_js("disableItem('MOVE')")
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
						self.base.ui.execute_js("disableItem('ATTACK')")
						self.mode = "NONE"
		elif self.mode == "STANCE":
			self.player.active_stance = self.player.stances[self.ui_selection]
			self.player.action_set.remove("STANCE")
			self.base.ui.execute_js("disableItem('STANCE')")
			self.ui_selection = 0
			self.base.ui.execute_js("switchToMenu('actions')")
			self.mode = "NONE"
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
			self.base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection)
			self.base.ui.execute_js("switchToMenu('stances')")

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
		self.uifx_selection.play()
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[1] += 1
		else:
			self.ui_selection -= 1

	def sel_left(self):
		self.uifx_selection.play()
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[0] -= 1

	def sel_down(self):
		self.uifx_selection.play()
		if self.mode in {"ATTACK", "MOVE"}:
			self.selected_pos[1] -= 1
		else:
			self.ui_selection += 1

	def sel_right(self):
		self.uifx_selection.play()
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
			self.base.change_state(EndCombatState)
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
					self.base.ui.execute_js("enableItem('%s')" % i)

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
			self.base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection)
			self.ui_last = self.ui_selection


class LobbyState(GameState):
	def __init__(self, _base):
		super(LobbyState, self).__init__(_base, 'lobby_ui')

		self.ui_options = [
			"STUDENT_INFO",
			"COURSEWORK",
			"OPTIONS",
			"QUIT",
		]
		self.mode = None
		self.base.ui.execute_js("setActiveTab(%d)" % self.ui_selection, True)

	def accept_selection(self):
		if self.mode is None:
			super(LobbyState, self).accept_selection()
			self.mode = self.ui_options[self.ui_selection]
			self.ui_selection = 0
	
			if self.mode == "STUDENT_INFO":
				pass
			elif self.mode == "COURSEWORK":
				self.base.change_state(CombatState)
			elif self.mode == "OPTIONS":
				pass
			elif self.mode == "QUIT":
				sys.exit()

	def escape(self):
		if self.mode is not None:
			super(LobbyState, self).escape()
			self.ui_selection = self.ui_options.index(self.mode)
			self.mode = None

	def main_loop(self):

		ui_max = 3
		if self.ui_selection > ui_max:
			self.ui_selection = 0
		elif self.ui_selection < 0:
			self.ui_selection = ui_max

		if self.ui_last != self.ui_selection:
			if self.mode is None:
				self.base.ui.execute_js("setActiveTab(%d)" % self.ui_selection)
			self.ui_last = self.ui_selection


class EndCombatState(GameState):
	def __init__(self, _base):
		super(EndCombatState, self).__init__(_base, 'end_combat_ui')

		# Generate some new spells
		self.new_stances = StanceGenerator.n_random(4)

		self.refresh_spell_ui()
		self.base.ui.execute_js("activeSpell('curr_spells', 0)", onload=True)
		self.base.ui.execute_js("activeSpell('gen_spells', 0)", onload=True)

		self.spell_list = 'curr_spells'
		self.last_selection = 0

	def refresh_spell_ui(self):
		stance_str = stances_to_json(self.player.stances)
		self.base.ui.execute_js("setupSpells('curr_spells', %s)" % stance_str, onload=True)

		stance_str = stances_to_json(self.new_stances)
		self.base.ui.execute_js("setupSpells('gen_spells', %s)" % stance_str, onload=True)

	def accept_selection(self):
		super(EndCombatState, self).accept_selection()
		if self.spell_list == 'curr_spells':
			self.spell_list = 'gen_spells'
		else:
			newstance = self.new_stances.pop(self.ui_selection)
			oldstance = self.player.stances.pop(self.last_selection)

			self.new_stances.insert(self.ui_selection, oldstance)
			self.player.stances.insert(self.last_selection, newstance)

			self.refresh_spell_ui()
			self.spell_list = 'curr_spells'
		self.last_selection, self.ui_selection = self.ui_selection, self.last_selection

	def escape(self):
		super(EndCombatState, self).escape()
		if self.spell_list == 'gen_spells':
			self.spell_list = 'curr_spells'
			self.last_selection, self.ui_selection = self.ui_selection, self.last_selection
		else:
			self.base.change_state(LobbyState)

	def main_loop(self):
		if self.spell_list == 'curr_spells':
			ui_max = len(self.player.stances) - 1
		else:
			ui_max = len(self.new_stances) - 1
		if self.ui_selection > ui_max:
			self.ui_selection = 0
		elif self.ui_selection < 0:
			self.ui_selection = ui_max

		if self.ui_last != self.ui_selection:
			self.base.ui.execute_js("activeSpell('%s', %d)" % (self.spell_list, self.ui_selection))
			self.ui_last = self.ui_selection


class TitleState(GameState):
	def __init__(self, _base):
		super(TitleState, self).__init__(_base, 'title_ui')

		self.ui_options = [
			"NEW",
			"LOAD",
			"OPTIONS",
			"QUIT",
		]
		self.mode = None
		self.base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection, True)

	def accept_selection(self):
		super(TitleState, self).accept_selection()
		if self.mode is None:
			self.mode = self.ui_options[self.ui_selection]

			if self.mode == "NEW":
				self.base.change_state(LobbyState)
			elif self.mode == "LOAD":
				self.base.change_state(LobbyState)
			elif self.mode == "OPTIONS":
				self.mode = None
			elif self.mode == "QUIT":
				sys.exit()

	def main_loop(self):
		ui_max = len(self.ui_options) - 1
		if self.ui_selection > ui_max:
			self.ui_selection = 0
		elif self.ui_selection < 0:
			self.ui_selection = ui_max

		if self.ui_last != self.ui_selection:
			self.base.ui.execute_js("setActiveSelection(%d)" % self.ui_selection)
			self.ui_last = self.ui_selection


class Game(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		self.accept("f1", sys.exit)
		self.win.setCloseRequestEvent("f1")

		self.ui = CEFPanda()

		self.player = None

		self.state = TitleState(self)

		self.taskMgr.add(self.main_loop, "MainLoop")

	def change_state(self, new_state):
		self.state.destroy()
		self.state = new_state(self)

	def main_loop(self, task):
		self.state.main_loop()
		return task.cont


app = Game()
app.run()