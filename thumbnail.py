#! /usr/bin/env python3
"""
"""
import os, os.path
import subprocess

def bw(arg, **kwargs):
	proc = subprocess.Popen(['djpeg', '-grayscale', '-scale', '1/8', arg], stdout=subprocess.PIPE)
	out, _ = proc.communicate()
	return [ ('BW', 1./8, out) ]
if __name__ == '__main__':
	import sys
	for arg in sys.argv[1:]:
		print(bw(arg))
# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
