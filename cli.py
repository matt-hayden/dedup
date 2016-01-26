#! /usr/bin/env python3

"""
"""

import os, os.path
import tarfile
import zipfile

import characterize


class Row:
	pass
def get_file_info(arg, quick=False, method=characterize.characterize, **kwargs):
	row = Row()
	row.filename = arg
	row.stat = os.stat(arg)
	with open(arg, 'rb') as fi:
		row.sums = set(method(fi,
							  size_hint=row.stat.st_size,
							  quick=quick))
		yield row
		if tarfile.is_tarfile(arg):
			yield from expand_tarfile(arg, **kwargs)
		elif zipfile.is_zipfile(arg):
			yield from expand_zipinfo(arg, **kwargs)
def expand_zipinfo(arg, method=characterize.characterize):
	with zipfile.ZipFile(arg) as zf:
		for internal_f in zf.infolist():
			if internal_f.filename.endswith('/'):
				continue
			row = Row()
#			row.comment		=	internal_f.comment
#			row.date_time	=	internal_f.date_time
			row.filename	=	arg
			row.member_name	=	internal_f.filename
#			row.ratio		=	float(internal_f.compress_size)/float(internal_f.file_size)
			row.sums = set(method(zf.open(internal_f),
								  size_hint=internal_f.file_size))
			row.sums.update( [ (('TOTAL', 'CRC'), internal_f.CRC) ] )
#			row.volume		=	internal_f.volume
			yield row
def expand_tarfile(arg, method=characterize.characterize):
	"""
		st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime
	"""
	with tarfile.open(arg) as tf:
		for internal_f in tf.getmembers():
			if not internal_f.isfile():
				continue
			row = Row()
			row.filename	=	arg
			row.membername	=	tf.name
			
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
			row.sums = set(method(internal_f.tobuf(),
								  size_hint=internal_f.size) )
			# internal_f also has islnk() and issym()
			yield row


if __name__ == '__main__':
	import shelve
	import sys

	import tqdm

	args = sys.argv[1:]

	with shelve.open('test.db') as db:
		def add(arg, db=db):
			for row in get_file_info(arg):
				if hasattr(row, 'member_name'):
					db[os.path.join(row.filename, row.member_name)] = row
				else:
					db[row.filename] = row
		for arg in tqdm.tqdm(args):
			if os.path.isdir(arg):
				for root, dirs, files in os.walk(arg):
					for f in files:
						add(os.path.join(root, f))
			elif os.path.isfile(arg):
				add(arg)
			else:
				print(arg, "invalid")
		

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
