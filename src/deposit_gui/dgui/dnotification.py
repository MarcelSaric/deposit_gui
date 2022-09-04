from PySide2 import (QtWidgets, QtCore, QtGui)

class DNotification(QtWidgets.QFrame):
	
	def __init__(self, parent):
		
		QtWidgets.QFrame.__init__(self)
		
		self._parent = parent
		self._delay = 2000
		
		self.label = QtWidgets.QLabel()
		
		self.setWindowFlags(QtCore.Qt.ToolTip)
		self.setFrameShape(QtWidgets.QFrame.StyledPanel)
		self.setStyleSheet('''
		QFrame { background-color: white;}
		QToolButton {
			margin: 0px 0px 0px 0px;
			border: none;
		}
		QLabel { 
			margin: 0px 10px 10px 10px; 
			font-size: 14px;
		}
		''')
		self.label.setOpenExternalLinks(True)
		
		close_button = QtWidgets.QToolButton()
		close_button.setIcon(QtWidgets.QApplication.style().standardIcon(
			QtWidgets.QStyle.SP_TitleBarCloseButton)
		)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(2, 2, 2, 2)
		self.layout().setSpacing(0)
		self.layout().addWidget(close_button)
		self.layout().addWidget(self.label)
		self.layout().setAlignment(close_button, QtCore.Qt.AlignRight)
		
		close_button.clicked.connect(self.on_close)
		
		self.hide_timer = QtCore.QTimer(singleShot = True, timeout = self.on_hide_timer)
		self.hide()
	
	def set_delay(self, delay):
		
		self._delay = delay
	
	def show(self, text, delay = None):
		
		if delay is not None:
			self._delay = delay
		pos = self._parent.mapToGlobal(self._parent.contentsRect().topRight())
		self.hide_timer.stop()
		self.label.setText(text)
		self.adjustSize()
		self.move(pos - self.rect().topRight() - QtCore.QPoint(5, -5))
		QtWidgets.QFrame.show(self)
		self.hide_timer.start(self._delay)
	
	@QtCore.Slot()
	def on_hide_timer(self):
		
		if self.frameRect().contains(self.mapFromGlobal(QtGui.QCursor.pos())):
			self.hide_timer.start(self._delay)
		else:
			self.hide()
	
	@QtCore.Slot()
	def on_close(self):
		
		self.hide_timer.stop()
		self.hide()
