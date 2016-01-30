#! /usr/bin/env python3

"""
"""
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


class FileObj:
	def __eq__(self, other):
		if hasattr(self, 'stat') and hasattr(other, 'stat'):
			if (cmp_stat(self.stat, other.stat) == 0):
				return True
		if self.matches(other):
			return True
		return False
	def matches(self, other, threshold=64):
		mc = get_match_code(self.sums, other.sums)
		return (threshold <= mc)
# pickle needs these to not be nested inside of a function or class
class TarFileObj(FileObj):
	pass
class ZipFileObj(FileObj):
	pass


def get_file_info(arg, method=characterize.get_characteristics, **kwargs):
	row = FileObj()
	row.filename = arg
	row.stat = STAT(arg)
	size = row.stat.st_size
	row.sums = set(method(arg, size_hint=size))
	if tarfile.is_tarfile(arg):
		row.members = dict(expand_tarfile(arg, **kwargs))
	elif zipfile.is_zipfile(arg):
		row.members = dict(expand_zipinfo(arg, **kwargs))
	return row

def expand_zipinfo(arg, method=characterize.get_characteristics):
	with zipfile.ZipFile(arg) as zf:
		for internal_f in zf.infolist():
			if internal_f.filename.endswith('/'): # dirs end in / across platforms?
				continue
			row = ZipFileObj()
			#row.mtime		=	internal_f.date_time
			row.filename	=	internal_f.filename
			row.size		=	internal_f.file_size
			if not row.size:
				continue
			row.sums		=	set( method(zf.open(internal_f), size_hint=row.size) )
			row.sums.update( [ (('TOTAL', 'CRC'), internal_f.CRC) ] )
			#row.volume		=	internal_f.volume
			yield os.path.join(arg, row.filename), row

def expand_tarfile(arg, method=characterize.get_characteristics, ignore_symlinks=True):
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
			row = TarFileObj()
			#row.mtime		=	internal_f.mtime
			row.filename	=	internal_f.name
			row.size		=	internal_f.size
			if not row.size:
				continue
			row.sums		=	set( method(internal_f.tobuf(), size_hint=row.size) )
			yield os.path.join(arg, row.filename), row


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
