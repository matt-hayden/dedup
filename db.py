#! /usr/bin/env python3

"""
"""
#from contextlib import contextmanager
import os, os.path
import shelve
import re

from futil import *

def cmp_stat(lhs, rhs):
	if lhs.st_size == rhs.st_size:
		if lhs.st_dev == rhs.st_dev:
			if lhs.st_ino == rhs.st_ino:
				assert lhs.st_mtime == rhs.st_mtime
				return 0
	if lhs.st_mtime < rhs.st_mtime:
		return 1
	if lhs.st_size < rhs.st_size:
		return 1
	return -1

class DatabaseError(Exception):
	pass

#@contextmanager
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
#	def __enter__(self):
#		self.open()
#	def __exit__(self):
#		self.close()

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
			new_stat = os.stat(fullpath)
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


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
