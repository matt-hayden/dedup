#! /usr/bin/env python3
"""
"""
import hashlib
import os, os.path

import adler_checksum

STAT = os.stat # lstat

MATCH_WEIGHTS = {}

tags = [ 'FOURCC',
		'FIRST_LINE',
		('PARTIAL', 'CRC'),
		('PARTIAL', 'adler32'),
		('PARTIAL', 'md5'),
		('PARTIAL', 'sha128'),
		('PARTIAL', 'sha224'),
		('PARTIAL', 'sha256'),
		('PARTIAL', 'sha384'),
		('PARTIAL', 'sha512'),
		'FINGERPRINT',
		('TOTAL', 'CRC'),
		('TOTAL', 'adler32'),
		'SIZE',
		('TOTAL', 'md5'),
		('TOTAL', 'sha128'),
		('TOTAL', 'sha224'),
		('TOTAL', 'sha256'),
		('TOTAL', 'sha384'),
		('TOTAL', 'sha512') ]
if __debug__: print('Checksum types and bitmask:')
i = 1
for tag in tags:
	if __debug__: print(tag, '=', i)
	MATCH_WEIGHTS[tag] = i
	i <<= 1

def pack_match_code(tag_items, lookup=MATCH_WEIGHTS, weight_upper_limit=i) -> int:
	bits = 0
	for t in tag_items:
		if t[0] in lookup:
			bits |= lookup[t[0]]
	return bits


def unpack_match_code(bits, lookup=MATCH_WEIGHTS):
	return [ k for k, v in lookup.items() if v & bits ]


THRESHOLD_FOR_MATCH = 2048|4096
THRESHOLD_FOR_EQUALITY = 8192|16384


class FastDigester:
	"""
	hfunction has update() and digest(), wrapped in this class
	"""
	hfunction = adler_checksum.Adler32 # override this in subclasses
	def __init__(self):
		self.h = self.hfunction()
		self.size = None
		self.results = []
	def update(self, b):
		self.h.update(b)
		if len(b):
			new_size = (self.size or 0) + len(b)
			self.results.append( (('PARTIAL', self.h.name), (self.size or 0, new_size), self.h.digest()) )
			self.size = new_size
	def digest(self):
		self.results.append( ('SIZE', self.size) )
		self.results.append( (('TOTAL', self.h.name), self.h.digest()) )
		return self.results

class ExhaustiveDigester:
	"""
	hfunction has update() and digest(), wrapped in this class
	"""
	hfunctions = [ hashlib.md5, hashlib.sha256 ] # override this in subclasses
	def __init__(self):
		self.hs = [ h() for h in self.hfunctions ]
		self.size = None
		self.results = []
	def update(self, b):
		for h in self.hs:
			h.update(b)
		if len(b):
			new_size = (self.size or 0) + len(b)
			for h in self.hs:
				self.results += [(('PARTIAL', h.name), (self.size or 0, new_size), h.digest())]
			self.size = new_size
	def digest(self):
		self.results += [('SIZE', self.size)]
		for h in self.hs:
			self.results += [(('TOTAL', h.name), h.digest())]
		return self.results

class FastDigester(ExhaustiveDigester):
	hfunctions = [ adler_checksum.Adler32 ]


__all__ = 'MATCH_WEIGHTS THRESHOLD_FOR_MATCH THRESHOLD_FOR_EQUALITY'.split()
__all__ += 'pack_match_code unpack_match_code STAT'.split()
# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
