#! /usr/bin/env python3
"""
"""
import os, os.path

import adler_checksum


def bytes_at_beginning_and_end(arg):
	"""Decide the number of bytes at beginning and end of a file, possibly by extension
	"""
	dirname, basename = os.path.split(arg)
	_, ext = os.path.splitext(basename)
	if ext.upper() in 'JPG JPEG':
		return 1024, 1024
	return 1024, 1024


def getfile(flo, ib, callback=None):
	head_length, tail_length = ib
	buffer_size = (1<<18)
	assert head_length < buffer_size
	assert tail_length < buffer_size
	try:
		size = flo.seek(0, 2)
		seekable = True
		if size == 0:
			return 0, b'', b''
		flo.seek(-tail_length, 2)
		tail_b = flo.read(tail_length)
		flo.seek(0, 0)
	except:
		seekable = False
		size = None
		tail_b = b''

	first_b = flo.read(buffer_size)
	head_b = first_b[:head_length]
	if (seekable and not callback) or (len(first_b) < buffer_size):
		return size, head_b, tail_b

	buffer_total = len(first_b)
	if callback: callback(first_b)
	prev_b, this_b = first_b, flo.read(buffer_size)
	while len(this_b) == buffer_size: # runs for second block ... last whole block
		buffer_total += buffer_size
		if callback: callback(this_b)
		prev_b, this_b = this_b, flo.read(buffer_size)

	# last block
	if len(this_b):
		last_b = this_b
		if callback: callback(last_b)
		buffer_total += len(last_b)
		if not tail_b and (len(last_b) < tail_length):
			offset = tail_length-len(last_b)
			tail_b = (prev_b[-offset:]+last_b)
	else:
		last_b = prev_b
	if not tail_b:
		tail_b = last_b[-tail_length:]
	if size is None:
		size = buffer_total
	else:
		assert size == buffer_total
	return size, (head_b, tail_b)


def gen_characteristics(flo, hfunction=adler_checksum.Adler32):
	h = hfunction()
	lines = []
	total = 0
	y = lines.append
	def my_update(b, y=y):
		nonlocal total # Python 3 only?
		h.update(b)
		y( (('PARTIAL', h.name), (total, total+len(b)), h.digest()) )
		total += len(b)
	if isinstance(flo, str):
		ib = bytes_at_beginning_and_end(flo)
		fdi = open(flo, 'rb')
	else:
		fdi = flo
		ib = (1024, 1024)
	head_length, tail_length = ib
	# callback may not be called for some files!
	size, (head_b, tail_b) = getfile(fdi, ib, callback=my_update)
	fdi.close()
	assert total == size
	y( ('SIZE', size) )
	y( (('TOTAL', h.name), h.digest()) )
	h = hfunction()
	h.update(head_b)
	y( (('PARTIAL', h.name), (0, head_length), h.digest()) )
	h = hfunction()
	h.update(tail_b)
	y( (('PARTIAL', h.name), (size-tail_length, tail_length), h.digest()) )
	
	return lines
	
if __name__ == '__main__':
	# test file is 1,000,000 byte file of zeroes
	results = gen_characteristics('testing/zeros.1M')
	print(results)
	assert (('TOTAL', 'adler32'), 1126236161) in results

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
