#! /usr/bin/env python3
"""
"""
import os, os.path

from __init__ import Digester
import adler_checksum
from util import getfile


class Adler32digester(Digester):
	hfunction = adler_checksum.Adler32
		
		
def gen_characteristics(arg, wrapper=Adler32digester):
	updater = wrapper()
	hfunction = wrapper.hfunction
	ib = (1024, 1024) # default
	if isinstance(arg, str):
		if os.path.isfile(arg):
			dirname, basename = os.path.split(arg)
			_, ext = os.path.splitext(basename)
			if ext.upper() in 'JPG JPEG':
				#y( ('THUMBNAIL', ...) )
				ib = 256, 256
				size = os.path.getsize(arg)
			elif ext.upper() in 'MP4 M4A':
				#y( ('FPCALC', ...) )
				ib = 1024, 1024
				size = os.path.getsize(arg)
			fdi = open(arg, 'rb')
	else:
		fdi = arg # better have .read()
	if ib:
		head_length, tail_length = ib
		# callback may not be called for some files!
		size, (head_b, tail_b) = getfile(fdi, ib, callback=updater.update)
		fdi.close()
	assert updater.size == size
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
	results = gen_characteristics('testing/zeros.1M')
	print(results)
	assert (('TOTAL', 'adler32'), 1126236161) in results

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
