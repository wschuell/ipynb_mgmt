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



class Template(object):
	def __init__(self, path, config_file='config'):
		self.path = path
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
		self.configs = template_module.get_nb_configs(config_file=self.config_file)

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
				for key,value in cfg.iteritems():
					for c in w['cells']:
						c['input'] = c['input'].replace('TEMPLATE_'+str(key),json.dumps(value,indent=2))
				example_cell = copy.deepcopy(w['cells'][0])
				example_cell.update(**self.first_cell(version=3))
				w['cells'] = [example_cell] + w['cells']
			nb_path = os.path.join(self.dirpath,'notebooks',self.short_name + '_' + cfg['name'] + '.ipynb')
			nbformat.write(nb_json, nb_path, 3)#, 'json')
			self.nb_list.append(Notebook(path=nb_path,json=nb_json))

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
		text = 'import os\nos.chdir(\'..\')\nfrom ' + self.name + ' import TemplateObjects\n\n\ntemplate_obj = TemplateObjects(config_file=\'' +self.config_file + '\')'
		if int(version) == 3:
			return {u'cell_type': u'code',
				'collapsed': False,
				'input': text,
				#'language': 'python',
				#u'metadata': {},
				u'outputs': [],
				#'prompt_number': None
				}
		elif int(version) == 4:
			return {u'cell_type': u'code',
				#'collapsed': False,
				#'input': text,
				'source':text,
				#'language': 'python',
				#u'metadata': {},
				u'outputs': [],
				'execution_count': None
				}
		else:
			return {}




class Notebook(object):
	def __init__(self,path,json=None,save_formats=['html']):
		self.path = path
		self.dirpath = os.path.dirname(os.path.dirname(self.path))
		self.name = os.path.basename(self.path)[:-6]
		if json is not None:
			self.nb_json = json
		else:
			self.nb_json = nbformat.read(path,3)#, 'json')
		self.save_formats = ['html']

	def run(self):
		runner = NotebookRunner(self.nb_json,working_dir=os.path.dirname(self.path))
		runner.run_notebook()
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





def execute_folder(folder, config_file='config'):
	tmp = Template(folder,config_file=config_file)
	tmp.do_all()
