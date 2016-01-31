#! /usr/bin/env python3
"""
"""
import os, os.path
import subprocess

def fpcalc(arg, encoding='UTF-8', **kwargs):
	proc = subprocess.Popen(['fpcalc', arg], stdout=subprocess.PIPE)
	out, _ = proc.communicate()
	lines = [ tuple(line.split('=', 1)) for line in out.decode(encoding).split('\n') if line ]
	return lines
if __name__ == '__main__':
	import sys
	for arg in sys.argv[1:]:
		print(fpcalc(arg))
# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
