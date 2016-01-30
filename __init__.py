#! /usr/bin/env python3

"""
"""

import hashlib
import os, os.path

import adler_checksum

STAT = os.stat # lstat

MATCH_WEIGHTS = {}
tags = 'FOURCC FIRST_LINE SIZE'.split()
#for x in 'CRC adler32 md5 sha128 sha224 sha256 sha384 sha512'.split():
#	tags.append( ('RUNNING', x) )
for x in 'CRC adler32 md5 sha128 sha224 sha256 sha384 sha512'.split():
	tags.extend( [ ('PARTIAL', x), ('TOTAL', x) ] )
i = 1
for tag in tags:
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


__all__ = 'MATCH_WEIGHTS pack_match_code unpack_match_code STAT'.split()
# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
