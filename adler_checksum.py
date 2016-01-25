#! /usr/bin/env python3

import zlib


class FakeHashFunction:
	name = ''
	def digest(self):
		return self.value
	def __init__(self):
		self.value = None
class Adler32(FakeHashFunction):
	name = 'adler32'
	def update(self, b, adler32=zlib.adler32):
		if self.value is None:
			self.value = adler32(b)
		else:
			self.value = adler32(b, self.value)


# vim: syntax=python tabstop=4 shiftwidth=4 softtabstop=4 number :
