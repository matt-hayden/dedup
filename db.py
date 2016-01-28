#! /usr/bin/env python3

"""
"""
import os, os.path
import shelve
import re

from futil import *


class DatabaseError(Exception):
	pass


class Database:
	def __init__(self, *args):
		self.db = {}
		self.filename = ''
		self.root = ''
		self.open(*args)
	def open(self, filename):
		dirname, basename = os.path.split(filename)
		self.filename = os.path.abspath(filename)
		self.root = os.path.abspath(dirname)
		self.db = shelve.open(filename or self.filename)
	def close(self):
		self.db.close()
	def add_entry(self, arg):
		if arg.startswith(self.root):
			fullpath, k = arg, arg[(len(self.root)+1):]
		else:
			k, fullpath = arg, os.path.join(self.root, arg)
		old_row = self.db.get(k, None)
		if old_row:
			if not os.path.exists(fullpath):
				del self.db[k]
				raise DatabaseError('{} -> {} not found'.format(arg, fullpath))
			new_stat = STAT(fullpath)
			if hasattr(old_row, 'stat'):
				if not cmp_stat(old_row.stat, new_stat): # returns -1 and 1 if different, 0 if identical
					return False
		self.db[k] = get_file_info(fullpath)
		return True
	def add_directory(self, arg, callback=None):
		for root, dirs, files in os.walk(arg, topdown=True):
			files = [ f for f in files if not f.startswith('.') ]
			dirs = [ d for d in dirs if not d.startswith('.') ]
			for f in files:
				fullpath = os.path.join(root, f)
				if self.add_entry(fullpath) and callback:
					callback(fullpath)
	def del_entry(self, arg):
		if arg in self.db:
			del self.db[arg]
			return True
		else:
			return False
	def refresh(self, pattern=''):
		if pattern:
			if isinstance(pattern, str):
				pattern = re.compile(pattern)
		for k in self.db:
			if pattern and not pattern.match(k):
				continue
			fullpath = os.path.join(self.root, k)
			self.add_entry(full_path)

	def dedup(self):
		"""Modified argument in-place, generating tuple of duplicates
		"""
		def is_valid(filename):
			if os.path.islink(filename):
				return False
			return True
		repl = {}
		while len(self.db):
			t_f, t_i = self.db.popitem()
			if not is_valid(t_f):
				continue
			for f, i in self.db.items():
				if not is_valid(f):
					continue
				if t_i == i:
					self.del_entry(f)
					yield f, i
			if hasattr(t_i, 'members'):
				for tm_f, tm_i in t_i.members.items():
					for f, i in self.db.items():
						if tm_i == i:
							self.del_entry(f)
							yield f, i
			repl[t_f] = t_i
		# at this point, self.db is empty
		self.db.update(repl)


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
