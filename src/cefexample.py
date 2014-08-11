from __future__ import print_function

from cefpython3 import cefpython
from panda3d.core import *

import os
import atexit


class CefClientHandler:
	browser = None
	texture = None

	def __init__(self, browser, texture):
		self.browser = browser
		self.texture = texture

	def OnPaint(self, browser, paintElementType, dirtyRects, buffer, width, height):
		if width != self.texture.get_x_size() or height != self.texture.get_y_size():
			return
		img = self.texture.modifyRamImage()
		if paintElementType == cefpython.PET_POPUP:
			print("width=%s, height=%s" % (width, height))
		elif paintElementType == cefpython.PET_VIEW:
			img.setData(buffer.GetString(mode="bgra", origin="bottom-left"))
		else:
			raise Exception("Unknown paintElementType: %s" % paintElementType)

	def GetViewRect(self, browser, rect):
		rect.append(0)
		rect.append(0)
		rect.append(self.texture.get_x_size())
		rect.append(self.texture.get_y_size())
		return True

	def OnLoadError(self, browser, frame, errorCode, errorText, failedURL):
		print("load error", browser, frame, errorCode, errorText, failedURL)


class CEFPanda(object):
	_UI_SCALE = 1.0

	def __init__(self):
		cefpython.Initialize({
			"log_severity": cefpython.LOGSEVERITY_INFO,
			"release_dcheck_enabled": True,  # Enable only when debugging
			# This directories must be set on Linux
			"locales_dir_path": cefpython.GetModuleDirectory()+"/locales",
			"resources_dir_path": cefpython.GetModuleDirectory(),
			"browser_subprocess_path": "%s/%s" % (
				cefpython.GetModuleDirectory(), "subprocess"),
		})
		self._cef_texture = Texture()
		self._cef_texture.set_compression(Texture.CMOff)
		self._cef_texture.set_component_type(Texture.TUnsignedByte)
		self._cef_texture.set_format(Texture.FRgba4)

		card_maker = CardMaker("browser2d")
		card_maker.set_frame(-self._UI_SCALE, self._UI_SCALE, -self._UI_SCALE, self._UI_SCALE)
		node = card_maker.generate()
		self._cef_node = render2d.attachNewNode(node)
		self._cef_node.set_texture(self._cef_texture)
		self._cef_node.set_transparency(TransparencyAttrib.MAlpha)

		winhnd = base.win.getWindowHandle().getIntHandle()
		wininfo = cefpython.WindowInfo()
		wininfo.SetAsOffscreen(winhnd)
		wininfo.SetTransparentPainting(True)

		url = "file://" + os.path.abspath("ui.html")
		self.browser = cefpython.CreateBrowserSync(
			wininfo,
			{},
			navigateUrl=url
		)
		self.browser.SetClientHandler(CefClientHandler(self.browser, self._cef_texture))

		self._set_browser_size()
		base.accept('window-event', self._set_browser_size)

		base.taskMgr.add(self._cef_message_loop, "CefMessageLoop")

		def shutdown_cef():
			cefpython.Shutdown()

		atexit.register(shutdown_cef)

	def _set_browser_size(self, window=None):
		width = int(round(base.win.getXSize() * self._UI_SCALE))
		height = int(round(base.win.getYSize() * self._UI_SCALE))
		self._cef_texture.set_x_size(width)
		self._cef_texture.set_y_size(height)

		# Clear the texture
		img = PNMImage(width, height)
		img.fill(0, 0, 0)
		img.alpha_fill(0)
		self._cef_texture.load(img)
		# img = CPTA_uchar(PTA_uchar.empty_array(self._cef_texture.get_expected_ram_image_size()))
		# self._cef_texture.set_ram_image(img)
		self.browser.WasResized()

	def _cef_message_loop(self, task):
		cefpython.MessageLoopWork()

		# if base.mouseWatcherNode.has_mouse():
		# 	mouse = base.mouseWatcherNode.getMouse()
		# 	rx, ry = mouse.get_x(), mouse.get_y()
		# 	x = (rx + 1.0) / 2.0 * self._cef_texture.get_x_size()
		# 	y = (ry + 1.0) / 2.0 * self._cef_texture.get_y_size()
		# 	y = self._cef_texture.get_y_size() - y
		# 	self.browser.SendMouseMoveEvent(x, y, mouseLeave=False)

		return task.cont
