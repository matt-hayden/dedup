#! /usr/bin/env python3
"""
"""
import collections
import os, os.path
import shelve
import shlex
import re

import characterize
from __init__ import *
from futil import *


DEFAULT_DB_FILENAME = '.dedup.db'

class DatabaseError(Exception):
	pass


class Database:
	def __init__(self, *args, **kwargs):
		self.db = {}
		self.filename = ''
		self.root = ''
		self.open(*args, **kwargs)
	def open(self, filename, root=''):
		dirname, basename = os.path.split(filename)
		self.filename = os.path.abspath(filename)
		self.root = root or os.path.abspath(dirname)
		self.db = shelve.open(filename or self.filename)
	def close(self):
		self.db.close()
	def add_entry(self, arg):
		fullpath = os.path.abspath(arg)
		if self.root:
			k = os.path.relpath(fullpath, self.root)
		else:
			k = arg
		old_row = self.db.get(k, None)
		if old_row:
			if not os.path.exists(fullpath):
				del self.db[k]
				raise DatabaseError('{} -> {} not found'.format(arg, fullpath))
			new_stat = STAT(fullpath)
			if hasattr(old_row, 'stat'):
				if not cmp_stat(old_row.stat, new_stat): # returns -1 and 1 if different, 0 if identical
					return False
		fi = get_file_info(fullpath)
		if fi:
			self.db[k] = fi
		elif k in self.db:
			del self.db
		return True
	def add_directory(self, arg, callback=None, ignore_dotfiles=True, ignore_symlinks=True):
		pathlist = []
		for root, dirs, files in os.walk(arg, topdown=True):
			if ignore_dotfiles:
				files = [ f for f in files if not f.startswith('.') ]
				dirs = [ d for d in dirs if not d.startswith('.') ]
			for f in files:
				relpath = os.path.join(root, f)
				if ignore_symlinks and os.path.islink(relpath):
					if __debug__: print(relpath, "is a symlink")
					continue
				pathlist.append(relpath)
		if __debug__: print("Found", len(pathlist), "files in", arg)
		if not len(pathlist):
			return
		for fp in pathlist:
			if __debug__: print(fp)
			if self.add_entry(fp) and callback:
				callback(fp)
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
			self.add_entry(fullpath)
	def get_sums_frequencies(self, recurse_archives=True):
		"""Returns (list of duplicates, list of uniques) characteristics found in the database
		"""
		freqs = collections.Counter()
		for vs in self.db.values():
			freqs.update(vs.sums)
			if recurse_archives and vs.members:
				for i in vs.members.values():
					freqs.update(i.sums)
		mc = freqs.most_common()
		for n, (i, c) in enumerate(mc):
			if c == 1:
				break
		if __debug__:
			print(len(mc)-n, "unique characteristics:")
			for c, _ in mc[n:]:
				print(c)
			print()
		return mc[:n], [ i for i, c in mc[n:] ]
	def get_possible_duplicates(self, min_weight=THRESHOLD_FOR_MATCH):
		"""Possible duplicates match to the degree perscribed by min_weight

		Does not recurse into archives
		"""
		nonunique_freqs, _ = self.get_sums_frequencies()
		search_chars = set()
		for c, _ in nonunique_freqs:
			w = MATCH_WEIGHTS.get(c[0])
			if w:
				if min_weight <= w:
					search_chars.update([c])
			else:
				if __debug__: print("Interestingly,", c, "is found but not weighted")
		if __debug__:
			print("non-unique characteristics:")
		for f, i in self.db.items():
			matches = i.sums & search_chars
			if matches:
				if __debug__: print(f, i, matches)
				yield f, i
	def get_duplicates(self, method=characterize.exhaustive, key=('TOTAL', 'md5')):
		"""Positive duplicates match to the degree perscribed by THRESHOLD_FOR_EQUALITY

		Does not recurse into archives
		"""
		for f, i in self.get_possible_duplicates():
			if key not in i.sums:
				ni = get_file_info(f, method=method)
				if ni:
					self.db[f] |= ni
		return self.get_possible_duplicates(min_weight=THRESHOLD_FOR_EQUALITY)
	def dedup(self, action='prune', exhaustive=True):
		"""Does not recurse into archives
		"""
		if action == 'prune':
			action = self.del_entry
		elif action == 'delete':
			def action(fn):
				print('$RM', shlex.quote(fn))
				self.del_entry(fn)
		dp = sorted(self.get_duplicates())
		if not exhaustive:
			yield from dp
		else:
			while len(dp):
				t_f, t_i = dp.pop(0)
				for (f, i) in dp[:]:
					if t_i == i:
						if __debug__: print(t_f,"==",f,"by",t_i.sums,"==",i.sums)
						dp.remove((f,i))
						if action: action(f)
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
	db = Database(db_file, root=root)
	return db


def refresh(arg):
	db = open_db(arg)
	db.add_directory(arg)
	db.refresh()
	return db


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
