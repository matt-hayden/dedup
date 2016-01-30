#! /usr/bin/env python3
"""
"""
import os, os.path

from __init__ import Digester
import adler_checksum
from util import getfile


class Adler32digester(Digester):
	hfunction = adler_checksum.Adler32
		
		
def get_characteristics(arg, size_hint=None, wrapper=Adler32digester):
	updater = wrapper()
	hfunction = wrapper.hfunction
	ib = (1024, 1024) # default
	size = None
	if hasattr(arg, 'read'):
		fdi = arg
	elif isinstance(arg, str):
		if os.path.isfile(arg):
			size = size_hint or os.path.getsize(arg)
			if size == 0:
				return [ ('SIZE', 0) ]
			dirname, basename = os.path.split(arg)
			_, ext = os.path.splitext(basename)
			if ext.upper() in 'JPG JPEG':
				#y( ('THUMBNAIL', ...) )
				ib = 256, 256
			elif ext.upper() in 'MP4 M4A':
				#y( ('FPCALC', ...) )
				ib = 1024, 1024
			fdi = open(arg, 'rb')
	else:
		raise ValueError(type(arg))
	assert (0, 0) < ib, "invalid heading and tailing"
	head_length, tail_length = ib
	if size < head_length:
		head_length = size
	if size < tail_length:
		tail_length = size
	ib = head_length, tail_length
	# callback may not be called for some files!
	read_size, (head_b, tail_b) = getfile(fdi, ib, callback=updater.update)
	if read_size == -1:
		results.append( ('TRUNCATED', True) )
	elif size is None:
		size = read_size
	else:
		assert read_size == size, "Expected {} bytes from {}, got {}".format(size, arg, read_size)
	assert 0 < read_size
	#fdi.close()
	assert updater.size == size, "Expected {} bytes from updater {}, got {}".format(size, updater, updater.size)
	results = updater.digest()

	h = hfunction()
	h.update(head_b)
	results.append( (('PARTIAL', h.name), (0, head_length), h.digest()) )
	h = hfunction()
	h.update(tail_b)
	results.append( (('PARTIAL', h.name), (size-tail_length, tail_length), h.digest()) )

	return results
	
if __name__ == '__main__':
	# test file is 1,000,000 byte file of zeroes
	#results = get_characteristics('testing/zeros.1M')
	results = get_characteristics('testing/seuss.pickle')
	print(results)
	print("Checksums match: ", (('TOTAL', 'adler32'), 1126236161) in results)

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
