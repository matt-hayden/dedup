#! /usr/bin/env python3

"""
"""
from datetime import datetime
import os, os.path
import tarfile
import zipfile

#from . import *
from __init__ import *
import characterize


def comm(lhs, rhs):
	"""Returns (left-only, common, right-only)
	"""
	com = lhs & rhs
	return (lhs-com), com, (rhs-com)


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


def get_match_code(lhs, rhs):
	_, com, _ = comm(lhs, rhs)
	return pack_match_code(com)


class Comparable:
	"""stat, sums
	"""
	def __eq__(self, other):
		if hasattr(self, 'stat') and hasattr(other, 'stat'):
			if (cmp_stat(self.stat, other.stat) == 0):
				return True
		if self.matches(other):
			return True
		return False
	def matches(self, other):
		return 1 <= self.get_match_value(other)
	def get_match_value(self, other, divisor=float(THRESHOLD_FOR_EQUALITY)):
		if isinstance(other, Comparable):
			mc = get_match_code(self.sums, other.sums)
		else:
			mc = get_match_code(self.sums, other)
		return mc/divisor
	def __and__(self, other):
		if isinstance(other, Comparable):
			return self.matches(other)
		else:
			return self.sums & set(other)
	def __ior__(self, other):
		# TODO: conservative
		assert self.stat == other.stat
		self.sums |= other.sums
		return self


class FileObj(Comparable):
	def __init__(self, my_stat):
		self.members	=	[]
		self.is_dup		=	None

		if my_stat:
			self.datetime	=	datetime.fromtimestamp(my_stat.st_mtime)
			self.size		=	my_stat.st_size
			self.stat		=	my_stat
		else:
			self.datetime	=	()
			self.size		=	None
			self.stat		=	()
	def get_flags(self):
		if hasattr(self, 'size'):
			if self.size in (0, None):
				yield '0'
		if hasattr(self, 'sums'):
			for tup in self.sums:
				label = tup[0]
				if 'TOTAL' in label:
					try:
						s = len(tup[-1])
						if 10 < s:
							yield 'H{}'.format(s)
					except TypeError:
						pass
					continue
			yield ' '
			for tup in self.sums:
				label = tup[0]
				if 'FINGERPRINT' in label:
					yield 'f'
				elif 'BW' in label:
					yield 't'
				elif 'COLOR' in label:
					yield 't'
		if hasattr(self, 'members'):
			if self.members:
				yield 'a'
		if hasattr(self, 'is_dup'):
			if self.is_dup:
				yield 'D'
	def describe(self):
		return [ self.datetime or '',
				 self.size,
				 ''.join(self.get_flags()) ]
	def __repr__(self):
		return "<File {1:,} b  modified {0:%c}  flags '{2}'>".format(*self.describe())
	def __str__(self):
		blank = ' '
		parts = zip(('{:%c}',	'{:12d}',	'{:>10}'),
					self.describe(),
					(24,		12,			10))
		return blank.join( (fs.format(s) if s else blank*fl) for fs, s, fl in parts)


def get_file_info(arg, sums=None, method=characterize.fast, method_for_archives=characterize.exhaustive):
	row = FileObj(STAT(arg))
	row.filename = arg
	if sums:
		row.sums = sums
	else:
		c = method(arg, size_hint=row.size)
		row.sums = set(c)
	if tarfile.is_tarfile(arg):
		row.members = dict(expand_tarfile(arg, method=method_for_archives))
	elif zipfile.is_zipfile(arg):
		row.members = dict(expand_zipinfo(arg, method=method_for_archives))
	return row

class ZipFileObj(FileObj):
	def __init__(self, zi):
		self.members	=	None
		# zi is a ZipInfo object
		dt				=	datetime(*zi.date_time)
		self.datetime	=	dt if (datetime(1980, 1, 1) < dt) else None
		self.filename	=	zi.filename
		self.size		=	zi.file_size
		self.volume		=	zi.volume
def expand_zipinfo(arg, method=characterize.fast):
	with zipfile.ZipFile(arg) as zf:
		for internal_f in zf.infolist():
			if internal_f.filename.endswith('/'): # dirs end in / across platforms?
				continue
			row = ZipFileObj(internal_f)
			if row.size == 0:
				continue
			row.sums		=	set( method(zf.open(internal_f), size_hint=row.size) )
			row.sums.update( [ (('TOTAL', 'CRC'), hex(internal_f.CRC)) ] )
			yield os.path.join(arg, row.filename), row


class TarFileObj(FileObj):
	def __init__(self, ti):
		self.members	=	None

		self.datetime	=	datetime.fromtimestamp(ti.mtime)
		self.filename	=	ti.name
		self.size		=	ti.size
def expand_tarfile(arg, method=characterize.fast, ignore_symlinks=True):
	"""
		st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime
	"""
	with tarfile.open(arg) as tf:
		for internal_f in tf.getmembers():
			if not internal_f.isfile():
				continue
			# internal_f also has islnk() and issym()
			if ignore_symlinks and internal_f.issym():
				continue
			row = TarFileObj(internal_f)
			if not row.size:
				continue
			row.sums		=	set( method(internal_f.tobuf(), size_hint=row.size) )
			yield os.path.join(arg, row.filename), row


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
