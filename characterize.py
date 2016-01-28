#! /usr/bin/env python3

"""
"""

## python hashlib uses openssl for sha-256
#import hashlib
#import imghdr
import os, os.path
#import sndhdr
import zipfile

import adler_checksum
from . import DEFAULT_BLOCK_SIZE, DEFAULT_HASH_FUNCTION


def characterize(flo,
	size_hint=None,
	limit=4.8E9,
	quick=None):
	"""	Generator for Python tuples. Identical files will produce
		no conflicting tuples.

	flo is a file-like object
	size_hint helps reduce buffering
	limit is the most bytes allowed, None or limit <= 0 implies no limit
	quick = True currently avoids loading the entire file when seekable
	"""
	block_size = kwargs.pop('block_size', DEFAULT_BLOCK_SIZE)
	eol = kwargs.pop('eol', b'\n') # b'\r\n' is possible
	# hfunction is initialized, update()d, and digest()ed
	hfunction = kwargs.pop('hfunction', DEFAULT_HASH_FUNCTION)
	limit = limit or 0
	seekable = None

	if kwargs:
		print(kwargs, "invalid")

	try:
		size = flo.seek(0, 2) # 2=end
		yield 'SIZE', size
		seekable = True
	except:
		size = size_hint or 0
		seekable = False
	offset, h = 0, hfunction()
	if seekable:
		if not size:
			raise StopIteration
		h1 = hfunction()
		if block_size < size:
			offset = flo.seek(-block_size, 2) # 2=end
			last_full_block = flo.read(block_size)
			if last_full_block:
				h1.update(last_full_block)
				yield ('PARTIAL', h1.name), (offset, size), h1.digest()
		flo.seek(0, 0) # 0=begin
		offset = 0
	# first block
	fb = flo.read(block_size) # bytes object
	first_block_size = len(fb)

	if 4 < first_block_size:
		yield 'FOURCC', fb[:4]
		if eol in fb[5:99]: # \n at position 4 is not considered, but [:4] could be returned
			fl, _ = fb[:99].split(eol, 1)
			if len(fl) != 4:
				yield 'FIRST_LINE', (offset, len(fl)), fl.rstrip()
	h.update(fb)
	if first_block_size < block_size:
		if not size:
			size = first_block_size
			yield 'SIZE', size
		yield ('TOTAL', h.name), (0, first_block_size), h.digest()
		raise StopIteration
	# main loop
	if size:
		whole_blocks, last_block_size = divmod(size, block_size)
		for bn in range(1, whole_blocks):
			h.update(flo.read(block_size))
			yield ('RUNNING', h.name), (offset, offset+block_size), h.digest()
			if quick:
				raise StopIteration
			offset += block_size
		lb = flo.read(last_block_size)
	else:
		prev_block, this_block = b'', fb
		while (len(this_block) == block_size):
			h.update(this_block)
			yield ('RUNNING', h.name), (offset, offset+block_size), h.digest()
			if (0 < limit < offset+block_size):
				yield 'MIN_SIZE', limit
				raise StopIteration
			offset += block_size
			prev_block, this_block = this_block, flo.read(block_size)
		assert this_block # last block, never returns empty
		lb = this_block
		last_block_size = len(lb)
		size = offset + last_block_size
		yield 'SIZE', size
		if last_block_size == block_size:
			last_full_block = lb
		else:
			last_full_block = (prev_block+lb)[-block_size:]
	# last block
	h.update(lb)
	yield ('RUNNING', h.name), (offset, size), h.digest()
	if not seekable:
		h2 = hfunction()
		h2.update(last_full_block)
		yield ('PARTIAL', h2.name), (size-block_size, size), h2.digest()

# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
