#! /usr/bin/env python3
"""Command-line interface
"""
import os, os.path
import shlex

from db import Database, ZipFileObj, TarFileObj

DEFAULT_DB_FILENAME = '.dedup.db'

class CLI(Database):
	def ls(self, pattern='', key=None):
		for f, i in self.get_by_pattern(pattern=pattern):
			prefix = ' | ' if isinstance(i, (TarFileObj, ZipFileObj)) else ''
			print(i, prefix, f)
	def process_duplicates(self, action='prune', quote=shlex.quote, **kwargs):
		dups = self.dedup(**kwargs)
		if 'prune' == action:
			raise StopIteration
		elif 'delete' == action:
			for _, dest in dups:
				yield '$RM', quote(dest)
		elif action in 'hardlink symlink softlink'.split():
			linker = '$LN' if 'hard' in action else '$LN -s'
			for src, dest in dups:
				yield '$RM', quote(dest)
				yield linker, quote(src), shlex.quote(dest)
		elif 'move' == action:
			for src, dest in dups:
				dirname, basename = os.path.split(dest)
				dd = os.path.join('DUPLICATES', dirname)
				os.makedirs(dd)
				if os.stat(dd).st_dev != os.stat(dest).st_dev:
					print("# Warning: moving", dest, "across devices")
				print('$MV', quote(dest), quote(dd))
		else:
			raise ValueError(action)
		
			yield f, i
		if recurse_archives and i.members:
			for af, ai in i.members.items():
				if pattern and not fnmatch.fnmatch(af, pattern):
					continue
				yield f, i


def open_db(arg=None):
	if arg is None:
		root = os.path.abspath('.')
		db_file = os.path.join(root, DEFAULT_DB_FILENAME)
	elif isinstance(arg, str):
		if os.path.isfile(arg):
			root, _ = os.path.split(arg)
			db_file = arg
		elif os.path.isdir(arg):
			root = arg
			db_file = os.path.join(root, DEFAULT_DB_FILENAME)
	else:
		raise ValueError(type(arg))
	if __debug__: print("opening Database({db_file}, root={root})".format(**locals()) )
	db = CLI(db_file, root=root)
	return db

		
if __name__ == '__main__':
	import sys
	args = sys.argv[1:]
	fdb = open_db(*args)

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
