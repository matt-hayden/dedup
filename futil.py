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


def get_file_info(arg, method=characterize.characterize, **kwargs):
	row = FileObj()
	row.filename = arg
	row.stat = STAT(arg)
	with open(arg, 'rb') as fi:
		row.sums = set(method(fi, size_hint=row.stat.st_size))
	if tarfile.is_tarfile(arg):
		row.members = dict(expand_tarfile(arg, **kwargs))
	elif zipfile.is_zipfile(arg):
		row.members = dict(expand_zipinfo(arg, **kwargs))
	return row

def expand_zipinfo(arg, method=characterize.characterize):
	with zipfile.ZipFile(arg) as zf:
		for internal_f in zf.infolist():
			if internal_f.filename.endswith('/'):
				continue
			row = ZipFileObj()
#			row.comment		=	internal_f.comment
#			row.date_time	=	internal_f.date_time
			row.filename	=	internal_f.filename
#			row.ratio		=	float(internal_f.compress_size)/float(internal_f.file_size)
			row.sums = set(method(zf.open(internal_f),
								  size_hint=internal_f.file_size))
			row.sums.update( [ (('TOTAL', 'CRC'), internal_f.CRC) ] )
#			row.volume		=	internal_f.volume
			yield os.path.join(arg, row.filename), row
def expand_tarfile(arg, method=characterize.characterize, ignore_symlinks=True):
	"""
		st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime
	"""
	with tarfile.open(arg) as tf:
		for internal_f in tf.getmembers():
			if not internal_f.isfile():
				continue
			if ignore_symlinks and internal_f.issym():
				continue
			row = TarFileObj()
			row.filename	=	internal_f.name
			'''
			row.stat = (internal_f.mode,	# st_mode
						-1,					# st_ino
						-1,					# st_dev
						None,				# st_nlink
						internal_f.uid,		# st_uid
						internal_f.gid,		# st_gid
						internal_f.size,	# st_size
						None,				# st_atime
						internal_f.mtime,	# st_mtime
						None				# st_ctime
						)
			'''
			row.sums = set(method(internal_f.tobuf(),
								  size_hint=internal_f.size) )
			# internal_f also has islnk() and issym()
			yield os.path.join(arg, row.filename), row


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
