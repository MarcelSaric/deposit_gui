from deposit_gui.dgui.abstract_subview import AbstractSubview

from PySide2 import (QtWidgets, QtCore, QtGui)

class VQueryToolbar(AbstractSubview):
	
	signal_entered = QtCore.Signal(str)
	
	def __init__(self, vmain) -> None:
		
		AbstractSubview.__init__(self, vmain)
		
		self.vmain.addToolBarBreak()
		self._toolbar = self.vmain.addToolBar("Query")
		
		self._query_box = QtWidgets.QComboBox()
		self._query_box.setEditable(True)
		self._query_box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		self._query_box.setMinimumHeight(26)
		self._query_box.completer().setCaseSensitivity(QtCore.Qt.CaseSensitive)
		
		self._toolbar.addWidget(QtWidgets.QLabel("Query: "))
		self._toolbar.addWidget(self._query_box)
		
		self._query_box.lineEdit().returnPressed.connect(self.on_enter)
	
	def set_query_text(self, text):
		
		self._query_box.setCurrentText(text)
	
	def get_query_text(self):
		
		return self._query_box.currentText().strip()
	
	@QtCore.Slot()
	def on_enter(self):
		
		text = self._query_box.currentText().strip()
		if text:
			self.signal_entered.emit(text)
