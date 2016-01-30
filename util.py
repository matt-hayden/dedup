#! /usr/bin/env python3
"""
"""


def getfile(flo, ib, callback=None, limit=4.8E9):
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
		return size, (head_b, tail_b)

	buffer_total = len(first_b)
	if callback: callback(first_b)
	prev_b, this_b = first_b, flo.read(buffer_size)
	while len(this_b) == buffer_size: # runs for second block ... last whole block
		if 0 < limit < buffer_total+buffer_size:
			size = -1
			tail_b = b''
			break
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


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
