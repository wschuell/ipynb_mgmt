from ._version import __version__

from runipy.notebook_runner import NotebookRunner
#from nbformat.current import read,write
#from nbformat.v4 import read_json,write_json
#from nbformat.v3 import read_json,write_json
#from nbformat.v3 import reads_json,writes_json
#from nbformat import read,write
from nbconvert import HTMLExporter
import codecs
import nbformat
import copy
import json
import os
from path import Path
#read = reads_json
#write =  writes_json
import copy
from importlib import import_module


import cProfile, pstats
try:
	import StringIO as io
except:
	import io

class Template(object):
	def __init__(self, path, config_file='config', profiling=False):
		self.path = path
		self.profiling = profiling
		self.config_file = config_file
		self.dirpath = os.path.dirname(path)
		self.name = os.path.basename(path)
		short = self.name.split('_')
		if 'template' in short:
			short.remove('template')
		self.short_name = ('_').join(short)
		self.template_json = nbformat.read(os.path.join(path,'_template.ipynb'),3)#, 'json')
		# clear output
		self.nb_list = []
		self.configs = []

	def get_configs(self):
		template_module = __import__(self.name)
		#try:
		self.configs = template_module.TemplateObjects.get_nb_configs(config_file=self.config_file)
		#except AttributeError:
		#	raise AttributeError('class TemplateObjects is absent')

	def generate(self):
		if self.configs and not os.path.isdir(os.path.join(self.dirpath,'notebooks')):
			os.makedirs(os.path.join(self.dirpath,'notebooks'))
		for cfg in self.configs:
			nb_json = copy.deepcopy(self.template_json)
			#for c in nb_json['cells']:
			#	c['source'] = c['source'].replace('TEMPLATE_'+key,json.dumps(value,indent=2))
			#example_cell = copy.deepcopy(nb_json['cells'][0])
			#nb_json['cells'] = [example_cell.update(**self.first_cell(version=4))] + nb_json['cells']
			for w in nb_json['worksheets']:
				example_cell = copy.deepcopy(w['cells'][0])
				example_cell.update(**self.first_cell(version=3))
				w['cells'] = [example_cell] + w['cells']
				for key,value in list(cfg.items()):
					for c in w['cells']:
						c['input'] = c['input'].replace('TEMPLATE_'+str(key),json.dumps(value,indent=2))
			nb_path = os.path.join(self.dirpath,'notebooks',self.short_name + '_' + cfg['name'] + '.ipynb')
			nbformat.write(nb_json, nb_path, 3)#, 'json')
			self.nb_list.append(Notebook(path=nb_path,json=nb_json,profiling=self.profiling))

	def run(self,n=None):
		if n is None:
			lst = self.nb_list
		else:
			lst = self.nb_list[:n]
		for nb in lst:
			nb.run()
			nb.save()

	def do_all(self):
		self.get_configs()
		self.generate()
		self.run()

	def first_cell(self,version=3):
		text = """import os
import sys
os.chdir(\'..\')
if not os.path.exists({work_dir}):
	os.makedirs({work_dir})
from {name} import TemplateObjects
template_obj = TemplateObjects(config_file={config_file},name=TEMPLATE_name)
os.chdir({work_dir})""".format(work_dir="\'work_dir\'",name=self.name,config_file=self.config_file)

		if int(version) == 3:
			return {'cell_type': 'code',
				'collapsed': False,
				'input': text,
				#'language': 'python',
				#u'metadata': {},
				'outputs': [],
				#'prompt_number': None
				}
		elif int(version) == 4:
			return {'cell_type': 'code',
				#'collapsed': False,
				#'input': text,
				'source':text,
				#'language': 'python',
				#u'metadata': {},
				'outputs': [],
				'execution_count': None
				}
		else:
			return {}




class Notebook(object):
	def __init__(self,path,json=None,save_formats=['html'],profiling=False):
		self.path = path
		self.profiling = profiling
		self.dirpath = os.path.dirname(os.path.dirname(self.path))
		self.name = os.path.basename(self.path)[:-6]
		if json is not None:
			self.nb_json = json
		else:
			self.nb_json = nbformat.read(path,3)#, 'json')
		self.save_formats = ['html']

	def run(self):
		runner = NotebookRunner(self.nb_json,working_dir=os.path.dirname(self.path))
		#self.start_profiler()
		try:
			runner.run_notebook()
		except:
			runner.km.shutdown_kernel(now=True)
			raise
		#self.stop_profiler()
		self.nb_json = runner.nb

	def save(self):
		nbformat.write(self.nb_json, self.path, 3)
		nb = nbformat.read(self.path, 3)
		nbformat.write(nb, self.path, 4)
		if 'html' in self.save_formats:
			if not os.path.isdir(os.path.join(self.dirpath,'html')):
				os.makedirs(os.path.join(self.dirpath,'html'))
			exporter = HTMLExporter()
			output_notebook = nbformat.read(self.path, as_version=4)
			output, resources = exporter.from_notebook_node(output_notebook)
			html_path = os.path.join(self.dirpath,'html',self.name+'.html')
			codecs.open(html_path, 'w', encoding='utf-8').write(output)
#		self.save_profile(filename=os.path.join(self.dirpath,'nb_profiles',self.name+'_profile.txt'))

	def headcell_profiling(self):
		return """import cProfile, pstats, StringIO
profiler = cProfile.Profile()
profiler.enable()"""

	def tailcell_profiling(self):
		return """profiler.disable()

s = StringIO.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
ps.print_stats()
filename='profile2.txt'
with open(filename,'w') as f:
    f.write(s.getvalue())
s.close()"""


#	def start_profiler(self):
#		if self.profiling:
#			self.profiler = cProfile.Profile()
#			self.profiler.enable()
#
#	def stop_profiler(self):
#		if self.profiling and hasattr(self,'profiler'):
#			self.profiler.disable()
#
#	def save_profile(self,filename):
#		if self.profiling and hasattr(self,'profiler'):
#			s = StringIO.StringIO()
#			sortby = 'cumulative'
#			ps = pstats.Stats(self.profiler, stream=s).sort_stats(sortby)
#			ps.print_stats()
#			if not os.path.isdir(os.path.dirname(filename)):
#				os.makedirs(os.path.dirname(filename))
#			with open(filename,'w') as f:
#				f.write(s.getvalue())
#			s.close()





def execute_folder(folder, config_file='config', profiling=True):
	tmp = Template(folder,config_file=config_file, profiling=profiling)
	tmp.do_all()




def cached(tempfun):
	def mod_fun(obj_self, *args, **kwargs):
		args_list = sorted([str(val) for val in list(args) + list(kwargs.values())])
		args_str = ''.join(args_list)
		try:
			return copy.deepcopy(obj_self._cache[tempfun.__name__+args_str])
		except KeyError:
			obj_self._cache[tempfun.__name__+args_str] = tempfun(obj_self, *args, **kwargs)
			return copy.deepcopy(obj_self._cache[tempfun.__name__+args_str])
	return mod_fun



class TemplateObjects(object):

	@classmethod
	def get_names_from_file(cls,config_file='config'):
		config = cls.configs.load(config_file)
		return config.names


	def __init__(self,config_file='config',name=''):
		self.name = name
		cls = self.__class__
		config = cls.configs.load(config_file)
		for v in cls.variables:
			try:
				val = getattr(config,v)
			except:
				print(v)
				print(config.__getattr__(v))
				raise
			setattr(self,v,val)
		self._cache = {}

	def nb_cfg(self,n=None):
		if n is None:
			n = self.name
		dict_cfg = {'name':n}
		return dict_cfg


	@classmethod
	def get_nb_configs(cls,config_file='config'):
		names = cls.get_names_from_file(config_file=config_file)
		return [cls(config_file=config_file,name=n).nb_cfg() for n in names]

class ConfigLoader(object):
	def load(self,filename):
		if isinstance(filename,list):
			conf_list = []
			for name in filename:
				conf_list.append(import_module('.'+name,package=__name__).Config())
			main_conf = conf_list[0]
			for m in range(1,len(conf_list)):
				c = conf_list[m]
				for att in dir(c):
					if att[0] != '_':
						setattr(main_conf,att,getattr(c,att))

			#def new_get_attr(attribute):
			#	for m in range(1,len(conf_list)):
			#		c = conf_list[m]
			#		if hasattr(c,attribute):
			#			return getattr(c,attribute)
			#main_conf.__getattr__ = new_get_attr
			return main_conf
		else:
			return import_module('.'+filename,package=__name__).Config()
