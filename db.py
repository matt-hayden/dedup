#! /usr/bin/env python3
"""
"""
import collections
import filecmp
import fnmatch
import os, os.path
import shelve
import re

import characterize
from __init__ import *
from futil import *


class DatabaseError(Exception):
	pass


class Database:
	def __init__(self, *args, **kwargs):
		self.db = {}
		self.filename = ''
		self.root = ''
		self.open(*args, **kwargs)
	def open(self, filename, root=''):
		if __debug__: print("Database.open('{filename}', root='{root}')".format(**locals()) )
		dirname, basename = os.path.split(filename)
		self.filename = os.path.abspath(filename)
		self.root = root or os.path.abspath(dirname)
		self.db = shelve.open(filename or self.filename)
	def close(self):
		self.db.close()
	def add_entry(self, arg, **kwargs):
		"""
		CRC=123
		adler32=4567
		md5=b'...'
		sha256=b'...'
		"""
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
		if kwargs:
			sums = { (('TOTAL', k), v) for k, v in kwargs.item() }
			fi = get_file_info(fullpath, sums)
		else:
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
		if not len(self.db):
			return (), ()
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
		Returns a list of (characteristic, [(filename, info), ...])
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
		if not len(search_chars):
			return []
		if __debug__:
			print("non-unique characteristics:")
		pd_by_char = collections.defaultdict(list)
		for f, i in self.db.items():
			matches = i.sums & search_chars
			if matches:
				if __debug__: print(f, repr(i), matches)
				pd_by_char[str(matches)] += [ (f, i) ]
		return pd_by_char.items()
	def get_duplicates(self, method=characterize.exhaustive, key=('TOTAL', 'md5')):
		"""Positive duplicates match to the degree perscribed by THRESHOLD_FOR_EQUALITY
		Returns a list of (characteristic, [(filename, info), ...])
		Does not recurse into archives
		"""
		for _, fis in self.get_possible_duplicates():
			for f, i in fis:
				if key not in i.sums:
					ni = get_file_info(f, method=method)
					if ni:
						self.db[f] |= ni
		return self.get_possible_duplicates(min_weight=THRESHOLD_FOR_EQUALITY)
	def dedup(self, prune=False, key=None):
		"""Does not recurse into archives
		"""
		if not len(self.db):
			raise StopIteration
		for _, fis in self.get_duplicates():
			fis.sort(key=key)
			while len(fis):
				t_f, t_i = fis.pop(0)
				for f, i in fis[:]:
					if __debug__: print("Exhaustively comparing", t_f, "and", f)
					if filecmp.cmp(t_f, f): # caches file comparisons
						fis.remove((f,i)) # i changes below
						if prune:
							self.del_entry(f)
						else:
							i.is_dup = True
							self.db[f] = i
						yield t_f, f
					elif not prune:
						i.is_dup = False
						self.db[f] = i
	def get_by_pattern(self, pattern='', recurse_archives=True, key=None):
		if not len(self.db):
			raise StopIteration
		if pattern:
			fis = sorted(( (f, i) for (f, i) in self.db.items() if fnmatch.fnmatch(f, pattern)), key=key)
		else:
			fis = sorted(self.db.items(), key=key)
		for f, i in fis:
			yield f, i
			members = i.members
			if recurse_archives and members:
				if pattern:
					fis = sorted(( (f, i) for (f, i) in members.items() if fnmatch.fnmatch(f, pattern)), key=key)
				else:
					fis = sorted(members.items(), key=key)
				yield from fis


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
