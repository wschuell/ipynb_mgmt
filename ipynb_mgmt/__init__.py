from ._version import __version__

from runipy.notebook_runner import NotebookRunner
from IPython.nbformat.current import read,write
from nbconvert import HTMLExporter
import codecs
import nbformat
import copy
import json


class Template(object):
	def __init__(self, path):
		self.path = path
		self.template_json = read(open(path), 'json')
		# clear output
		self.nb_list = []
		self.configs = []

	def get_configs(self):
		cfg_path = self.path[:-6] + '_cfg'
		cfg_py = __import__(cfg_path)
		self.configs = cfg_py.get_configs()

	def generate(self):
		for cfg in self.configs:
			nb_json = copy.deepcopy(self.template_json)
			for key,value in cfg.iteritems():
				for w in nb_json['worksheets']:
					for c in w['cells']:
						c['input'] = c['input'].replace('TEMPLATE_'+key,json.dumps(value,indent=2))
			nb_path = self.path[:-15] + '_' + cfg['name'] + '.ipynb' # tmp path has to end in _template.ipynb
			write(nb_json, open(nb_path, 'w'), 'json')
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





class Notebook(object):
	def __init__(self,path,json=None,save_formats=['html']):
		self.path = path
		if json is not None:
			self.nb_json = json
		else:
			self.nb_json = read(open(path), 'json')
		self.save_formats = ['html']

	def run(self):
		runner = NotebookRunner(self.nb_json)
		runner.run_notebook()
		self.nb_json = runner.nb

	def save(self):
		write(self.nb_json, open(self.path, 'w'), 'json')
		if 'html' in self.save_formats:
			exporter = HTMLExporter()
			output_notebook = nbformat.read(self.path, as_version=4)
			output, resources = exporter.from_notebook_node(output_notebook)
			html_path = self.path[:-5]+'html'
			codecs.open(html_path, 'w', encoding='utf-8').write(output)

