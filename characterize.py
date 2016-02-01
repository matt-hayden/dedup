#! /usr/bin/env python3
"""
"""
import os, os.path

from __init__ import Digester
import adler_checksum
from util import getfile
import fpcalc
import thumbnail

class Adler32digester(Digester):
	hfunction = adler_checksum.Adler32
		
		
def get_characteristics(arg, size_hint=None, wrapper=Adler32digester):
	"""
	size_hint is used if other means fail
	wrapper can be a class that implements update() and digest(), with an hfunction like hashlib.md5
	"""
	updater = wrapper()
	hfunction = wrapper.hfunction
	ib = 1024, 1024 # default
	size = None
	def check():
		nonlocal ib
		nonlocal size
		assert (0, 0) < ib, "invalid heading and tailing"
		if size is None:
			return
		if (size,)*2 < ib:
			ib = size, ib[-1]
		if (size,)*2 < ib:
			ib = ib[0], size
	results = []
	if hasattr(arg, 'read'):
		fdi = arg
	elif isinstance(arg, str):
		if os.path.isfile(arg):
			dirname, basename = os.path.split(arg)
			_, ext = os.path.splitext(basename)
			try:
				size = os.path.getsize(arg)
			except: # OSError:
				if __debug__: print("Failed to get size of", arg)
				size = size_hint
			if size == 0:
				return [ ('SIZE', 0) ]
			if ext.upper() in '.JPG .JPEG':
				try:
					results += thumbnail.bw(arg)
				except: # OSError as e:
					if __debug__: print('thumbnail failed')
				ib = 256, 256
			elif ext.upper() in '.MP3 .MP4 .M4A .WAV':
				try:
					fp = dict(fpcalc.fpcalc(arg))
					results += [ ('FINGERPRINT', int(fp['DURATION']), fp['FINGERPRINT']) ]
				except: # OSError as e:
					if __debug__: print('fpcalc failed')
				ib = 1024, 1024
			fdi = open(arg, 'rb')
	else:
		raise ValueError(type(arg))

	check()

	# callback may not be called for some files!
	read_size, (head_b, tail_b) = getfile(fdi, ib, callback=updater.update)
	if read_size == -1:
		if __debug__: print(fdi, "truncated to size", size)
		results.append( ('TRUNCATED', size) )
		fdi.close()
	elif size is None:
		size = read_size
		fdi.close()
	else:
		assert read_size == size, "Expected {} bytes from {}, got {}".format(size, arg, read_size)
	assert 0 < read_size
	assert updater.size == size, "Expected {} bytes from updater {}, got {}".format(size, updater, updater.size)
	results += updater.digest()

	check()

	h = hfunction()
	h.update(head_b)
	results.append( (('PARTIAL', h.name), (0, ib[0]), h.digest()) )
	h = hfunction()
	h.update(tail_b)
	results.append( (('PARTIAL', h.name), (size-ib[-1], size), h.digest()) )

	return results
	
if __name__ == '__main__':
	# test file is 1,000,000 byte file of zeroes
	#results = get_characteristics('testing/zeros.1M')
	results = get_characteristics('testing/seuss.pickle')
	print(results)
	print("Checksums match: ", (('TOTAL', 'adler32'), 1126236161) in results)

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
