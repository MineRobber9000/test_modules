# all of the imports!
from requests import get # to get the code
from enum import auto, IntEnum # for state
from importlib.machinery import ModuleSpec # for importlib shenanigans
from urllib.parse import urljoin # for getting the path to the code
from os.path import join # for getting the path to the code

# Tells what state the importer is in.
# USER - this is the top level user package
# REPO - this is the second-level repo package
# FILE - this is the actual file import
class GithubImportState(IntEnum):
	USER=auto()
	REPO=auto()
	FILE=auto()

class GithubImportFinder:
	def find_spec(self, modname, path=None, mod=None):
		package, dot, module = modname.rpartition(".")
		if not dot: # user level
			spec = ModuleSpec(modname, GithubImportLoader(), origin="https://github.com/"+module, loader_state=GithubImportState.USER, is_package=True)
			spec.submodule_search_locations = []
			return spec
		else:
			user, dot2, repo = package.rpartition(".")
			if not dot2: # repo level
				spec = ModuleSpec(modname, GithubImportLoader(), origin="https://github.com/"+"/".join([package,module]), loader_state=GithubImportState.REPO, is_package=True)
				spec.submodule_search_locations = []
				return spec
            # file level
			path = urljoin("https://github.com", join(user, repo, "raw", "master", module+".py"))
			return ModuleSpec(modname, GithubImportLoader(), origin=path, loader_state=GithubImportState.FILE)

class GithubImportLoader:
	def create_module(self, spec):
		return None # default semantics
	def exec_module(self, module):
		path = module.__spec__.origin
		if module.__spec__.loader_state!=GithubImportState.USER:
			setattr(sys.modules[module.__package__], module.__name__.rpartition(".")[-1], module)
		if module.__spec__.loader_state==GithubImportState.FILE:
			# load the module
			code = get(path)
			if code.status_code!=200:
				print(path, code)
				raise ModuleNotFoundError(f"No module named {module.__name__}")
			code = code.text
			exec(code, module.__dict__)

import sys

FINDER = GithubImportFinder()
sys.meta_path.append(FINDER)
