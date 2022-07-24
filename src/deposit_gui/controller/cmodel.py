from deposit_gui.dgui.abstract_subcontroller import AbstractSubcontroller
from deposit_gui.model.model import Model

from deposit import (DDateTime, DGeometry, DResource)
from deposit.datasource import AbstractDatasource

from deposit.utils.fnc_files import (as_url)
from deposit.utils.fnc_serialize import (try_numeric, value_to_str, select_to_class_descr)
from deposit.query.parse import (remove_bracketed_selects, extract_expr_vars)

from PySide2 import (QtCore)
from collections import defaultdict
from natsort import natsorted

class CModel(AbstractSubcontroller):
	
	def __init__(self, cmain) -> None:
		
		AbstractSubcontroller.__init__(self, cmain)
		
		self._model = Model()
		
		self._model.signal_added.connect(self.on_added)
		self._model.signal_deleted.connect(self.on_deleted)
		self._model.signal_changed.connect(self.on_changed)
		self._model.signal_saved.connect(self.on_saved)
		self._model.signal_loaded.connect(self.on_loaded)
		self._model.signal_local_folder_changed.connect(self.on_local_folder_changed)
		self._model.signal_queries_changed.connect(self.on_queries_changed)
		self._model.signal_user_tools_changed.connect(self.on_user_tools_changed)
	
	# ---- Signal handling
	# ------------------------------------------------------------------------
	@QtCore.Slot(list)
	def on_added(self, objects, classes):
		# elements = [DObject, DClass, ...]
		
		if classes:
			self.cmain.cnavigator.populate_classes()
			self.cmain.cmdiarea.update_class_graphs()
		self.cmain.cmdiarea.update_queries(objects, classes)
		self.cmain.cusertools.on_data_changed()
	
	@QtCore.Slot(list)
	def on_deleted(self, objects, classes):
		# elements = [obj_id, name, ...]
		
		if classes:
			self.cmain.cnavigator.populate_classes()
			self.cmain.cmdiarea.update_class_graphs()
		self.cmain.cmdiarea.update_queries(objects, classes)
		self.cmain.cusertools.on_data_changed()
	
	@QtCore.Slot(list)
	def on_changed(self, objects, classes):
		# elements = [DObject, DClass, ...]
		
		if classes:
			self.cmain.cnavigator.populate_classes()
			self.cmain.cmdiarea.update_class_graphs()
		self.cmain.cmdiarea.update_queries(objects, classes)
		self.cmain.cusertools.on_data_changed()
	
	@QtCore.Slot(object)
	def on_saved(self, datasource):
		
		self.cmain.cview.set_status_message("Saved: %s" % (str(datasource)))
	
	@QtCore.Slot()
	def on_loaded(self):
		
		self.update_model_info()
		self.cmain.cactions.update()
		self.cmain.cmdiarea.close_all()
		self.cmain.cnavigator.populate_classes()
		self.cmain.cnavigator.populate_queries()
		self.cmain.cusertools.populate_tools()
		self.cmain.cusertools.on_data_changed()
	
	@QtCore.Slot()
	def on_local_folder_changed(self):
		
		self.update_model_info()
		self.cmain.cactions.update()
	
	@QtCore.Slot()
	def on_queries_changed(self):
		
		self.cmain.cnavigator.populate_queries()
	
	@QtCore.Slot()
	def on_user_tools_changed(self):
		
		self.cmain.cusertools.populate_tools()
	
	
	# ---- get/set
	# ------------------------------------------------------------------------
	
	# ---- General
	# ------------------------------------------------------------------------
	def get_descriptor_names(self):
		
		return self._model.get_descriptor_names(ordered = True)
	
	def get_relation_labels(self):
		
		return self._model.get_relation_labels()
	
	def reverse_relation(self, label):
		
		if label.startswith("~"):
			return label[1:]
		return "~" + label
	
	def get_subgraph(self, objects):
		
		self.cmain.cview.progress.show("Extracting Subgraph")
		store = self._model.get_subgraph(objects, progress = self.cmain.cview.progress)
		self.cmain.cview.progress.stop()
		return store
	
	def get_thumbnail(self, resource, size = 256):
		
		return self._model.get_thumbnail(resource, size)
	
	def get_folder(self):
		
		return self._model.get_folder()
	
	def get_temp_copy(self, resource):
		
		return self._model.get_temp_copy(resource)
	
	def get_updated_url(self, resource):
		
		return self._model.get_updated_url(resource)
	
	def get_query(self, querystr):
		
		self.cmain.cview.progress.show("Processing Query")
		query = self._model.get_query(querystr, progress = self.cmain.cview.progress)
		self.cmain.cview.progress.stop()
		return query
	
	def has_local_folder(self):
		
		return self._model.has_local_folder()
	
	def set_local_folder(self, path):
		
		self._model.set_local_folder(path, progress = self.cmain.cview.progress)
	
	def prune_resources(self):
		
		self.cmain.cview.progress.show("Pruning Resources")
		self._model.prune_resources()
		self.cmain.cview.progress.stop()
	
	def can_save(self):
		
		datasource = self._model.get_datasource()
		
		return datasource.__class__.__name__ != "Memory"
	
	def update_model_info(self):
		
		texts = []
		texts.append("Data Source: <b>%s</b>" % (str(self._model.get_datasource())))
		folder = "Not set"
		if self._model.has_local_folder():
			folder = str(self._model.get_folder())
		texts.append("Local Folder: <b>%s</b>" % (folder))
		self.cmain.cmdiarea.set_background_text("".join([("<p>%s</p>" % text) for text in texts]))
		self.cmain.cview.set_title(self.get_datasource_name())
	
	def update_recent(self, kwargs):
		
		datasource = kwargs.get("datasource", None)
		if isinstance(datasource, AbstractDatasource):
			kwargs.update(datasource.to_dict())
		
		url = kwargs.get("url", None)
		if not url:
			path = kwargs.get("path", None)
			if path:
				url = as_url(path)
		self.cmain.cview._view.add_recent_connection(
			url = url,
			identifier = kwargs.get("identifier", None),
			connstr = kwargs.get("connstr", None),
		)
	
	def field_calculator(self, target, expr, rows):
		
		if (not target) or (not expr) or (not rows):
			return
		classes = set(self.get_class_names())
		descriptors = set(self.get_descriptor_names())
		expr, bracketed_selects = remove_bracketed_selects(expr, classes, descriptors)
		expr, vars = extract_expr_vars(expr.strip(), classes, descriptors, bracketed_selects)
		for obj_id in rows:
			obj = self.get_object(obj_id)
			values = dict(
				DDateTime = DDateTime,
				DGeometry = DGeometry,
				DResource = DResource,
			)
			for name in vars:
				values[name] = rows[obj_id].get(vars[name], None)
			value = eval(expr, values)
			if value is not None:
				obj.set_descriptor(target, value)
	
	def merge_objects(self, objects):
		# objects = [obj_id, ...]
		
		data = {}
		locations = {}
		relations = set()
		for obj_id in objects:
			obj = self.get_object(obj_id)
			for descr in obj.get_descriptors():
				if descr not in data:
					value = obj.get_descriptor(descr)
					if value is not None:
						data[descr] = value
						location = obj.get_location(descr)
						if location is not None:
							locations[descr] = location
		for obj_id in objects[1:]:
			obj = self.get_object(obj_id)
			for obj_tgt, label in obj.get_relations():
				weight = obj.get_relation_weight(obj_tgt, label)
				relations.add((obj_tgt, label, weight))
		obj = self.get_object(objects[0])
		for descr in data:
			obj.set_descriptor(descr, data[descr])
		for descr in locations:
			obj.set_location(descr, locations[descr])
		for obj_tgt, label, weight in relations:
			obj.add_relation(obj_tgt, label, weight)
		for obj_id in objects[1:]:
			self.del_object(obj_id)
	
	def merge_identical(self, objects):
		# objects = set(obj_id, ...)
		
		grouped = defaultdict(set)
		for obj_id in objects:
			obj = self.get_object(obj_id)
			key = [(descr.name, value_to_str(obj.get_descriptor(descr))) for descr in obj.get_descriptors()]
			grouped[tuple(sorted(key, key = lambda item: item[0]))].add(obj)
		for key in grouped:
			if len(grouped[key]) > 1:
				obj = grouped[key].pop()
				relations = set()
				for obj2 in grouped[key]:
					for obj_tgt, label in obj.get_relations():
						weight = obj.get_relation_weight(obj_tgt, label)
						relations.add((obj_tgt, label, weight))
				for obj_tgt, label, weight in relations:
					obj.add_relation(obj_tgt, label, weight)
				for obj2 in grouped[key]:
					self.del_object(obj2)
	
	def duplicate(self, objects):
		# objects = set(obj_id, ...)
		
		for obj_id in objects:
			obj = self.get_object(obj_id)
			obj2 = self.add_object()
			for descr in obj.get_descriptors():
				obj2.set_descriptor(descr, obj.get_descriptor(descr))
				location = sobj.get_location(descr)
				if location is not None:
					obj2.set_location(descr, location)
			for cls in obj.get_classes():
				cls.add_member(obj2)
	
	
	# ---- Object
	# ------------------------------------------------------------------------
	def add_object(self):
		
		return self._model.add_object()
	
	def get_object(self, obj_id):
		
		return self._model.get_object(obj_id)
	
	def del_object(self, obj_id):
		
		self._model.del_object(obj_id)
	
	
	# ---- Class
	# ------------------------------------------------------------------------
	def add_class(self, name):
		
		return self._model.add_class(name)
	
	def get_class(self, name):
		
		return self._model.get_class(name)
	
	def get_classes(self):
		
		return self._model.get_classes(ordered = True)
	
	def get_class_names(self, ordered = False):
		
		return self._model.get_class_names(ordered)
	
	def get_class_values(self, class_name, descriptor_name):
		
		values = set()
		cls = self._model.get_class(class_name)
		if cls is None:
			return []
		for obj in cls.get_members():
			val = obj.get_descriptor(descriptor_name)
			if val is not None:
				values.add(val)
		values = natsorted(values)
		
		return values
	
	def get_descriptor_names(self, ordered = False):
		
		return self._model.get_descriptor_names(ordered)
	
	def rename_class(self, cls, name):
		
		self._model.rename_class(cls, name)
	
	def rename_class_descriptor(self, descr, cls, name):
		
		self._model.rename_class_descriptor(descr, cls, name)
	
	def shift_class(self, cls, direction):
		
		if direction not in [1, -1]:
			return
		classes = self.get_classes()
		if cls not in classes:
			return
		idx = classes.index(cls)
		cls2 = None
		if direction == 1:
			if idx == 0:
				return
			cls2 = classes[idx - 1]
		elif direction == -1:
			if idx == len(classes) - 1:
				return
			cls2 = classes[idx + 1]
		if cls2 is not None:
			self._model.switch_order(cls, cls2)
	
	def del_class(self, name):
		
		self._model.del_class(name)
	
	def del_class_descriptor(self, descr, cls, class_only = False):
		
		self._model.del_class_descriptor(descr, cls, class_only)
	
	
	# ---- Import
	# ------------------------------------------------------------------------
	
	def add_data_row(self, data, relations = set(), unique = set()):
		# add multiple objects with classes at once & automatically add relations 
		#	based on class relations or as specified in the relations attribute
		# data = {(Class name, Descriptor name): value, ...}
		# relations = {(Class name 1, label, Class name 2), ...}
		# unique = {Class, ...}; always add a new object to classes 
		#	specified here, otherwise re-use objects with identical descriptors
		#
		# returns number of added Objects
		
		return self._model.add_data_row(data, relations, unique)
	
	def import_data(self, get_data, n_rows, targets, relations, unique):
		# get_data(row, col) = value
		# targets = {col: (class_name, descriptor_name), ...}
		# relations = {(Class name 1, label, Class name 2), ...}
		# unique = {Class, ...}
		#
		# returns number of imported Objects
		
		n_added = 0
		for row in range(n_rows):
			data_row = {}  # {(Class name, Descriptor name): value, ...}
			for col in targets:
				value = try_numeric(get_data(row, col))
				if (value is None) or (value == ""):
					continue
				data_row[targets[col]] = value
			if data_row:
				n_added += self._model.add_data_row(data_row, relations, unique)
		return n_added
	
	def import_store(self, store, unique = set()):
		# unique = {Class name, ...}; always add a new object to classes 
		#	specified here, otherwise re-use objects with identical descriptors
		# progress = DProgress
		
		self._model.import_store(store, unique, progress = self.cmain.cview.progress)
	
	
	# ---- User Tools
	# ------------------------------------------------------------------------
	def add_user_tool(self, user_tool):
		
		self._model.add_user_tool(user_tool)
	
	def get_user_tools(self):
		
		return self._model.get_user_tools()
	
	def del_user_tool(self, label):
		
		self._model.del_user_tool(label)
	
	
	# ---- Saved Query
	# ------------------------------------------------------------------------
	def add_saved_query(self, title, querystr):
		
		self._model.add_saved_query(title, querystr)
	
	def get_saved_query(self, title):
		
		return self._model.get_saved_query(title)
	
	def get_saved_queries(self):
		
		return self._model.get_saved_queries()
	
	def del_saved_query(self, title):
		
		self._model.del_saved_query(title)
	
	
	# ---- Persistence
	# ------------------------------------------------------------------------
	def get_datasource(self):
		
		return self._model.get_datasource()
	
	def get_datasource_name(self):
		
		return self._model.get_datasource().get_name()
	
	def save(self, *args, **kwargs):
		
		self.cmain.cview.progress.show("Saving")
		if self._model.save(progress = self.cmain.cview.progress, *args, **kwargs):
			self.cmain.cview.progress.stop()
			self.update_recent(kwargs)
			return True
		self.cmain.cview.progress.stop()
		return False
	
	def load(self, *args, **kwargs):
		# datasource = Datasource or format
		
		self.cmain.cview.progress.show("Loading")
		if self._model.load(progress = self.cmain.cview.progress, *args, **kwargs):
			self.cmain.cview.progress.stop()
			self.update_recent(kwargs)
			return True
		self.cmain.cview.progress.stop()
		return False
