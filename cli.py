#! /usr/bin/env python3
"""Command-line interface
"""
import os, os.path
import shlex

from db import Database, ZipFileObj, TarFileObj

DEFAULT_DB_FILENAME = '.dedup.db'

class CLI(Database):
	def ls(self, pattern='', key=None):
		if isinstance(key, str):
			if 'size' == key:
				def key(t):
					f, i = t
					try:
						return i.size
					except TypeError:
						return 0
			elif 'time' == key:
				def key(t):
					f, i = t
					try:
						return i.datetime.timetuple()
					except TypeError:
						return ()
			else:
				raise ValueError(key)
		total_size = 0
		for f, i in self.get_by_pattern(pattern=pattern, key=key):
			prefix = ''
			if isinstance(i, (TarFileObj, ZipFileObj)):
				prefix = ' |'
			else:
				total_size += i.size
			print(i, prefix, f)
		print("Total: {:,} b".format(total_size))
	def process_duplicates(self, action, quote=shlex.quote, **kwargs):
		if 'prune' == action:
			dups = self.dedup(prune=True, **kwargs)
			raise StopIteration
		else:
			dups = self.dedup(prune=False, **kwargs)
		if 'delete' == action:
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
		elif None != action:
			raise ValueError(action)

def open_db(arg=None):
	if arg is None:
		root = os.path.abspath('.')
		db_file = DEFAULT_DB_FILENAME
	elif isinstance(arg, str):
		if os.path.isfile(arg):
			root, _ = os.path.split(arg)
			db_file = arg
		elif os.path.isdir(arg):
			root = arg
			db_file = DEFAULT_DB_FILENAME
		if root:
			if __debug__: print("chdir({})".format(root))
			os.chdir(root)
	else:
		raise ValueError(type(arg))
	db = CLI(db_file)
	return db

		
if __name__ == '__main__':
	import sys
	args = sys.argv[1:]
	ocwd = os.getcwd()
	fdb = open_db(*args)

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
