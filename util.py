#! /usr/bin/env python3
"""
"""


def getfile(arg, ib, callback=None, limit=4.8E9, buffer_size=(1<<17)):
	head_length, tail_length = ib
	while (buffer_size < head_length) or (buffer_size < tail_length):
		buffer_size <<= 1
	head_b = tail_b = b''
	seekable = False
	size = None

	if hasattr(arg, 'read'):
		fdi = arg
	elif isinstance(arg, str):
		if os.path.isfile(arg):
			size = os.path.getsize(arg)
			seekable = True
		fdi = open(arg, 'rb', buffering=buffer_size)
	else:
		raise ValueError(type(fdi))

	if not seekable:
		try:
			size = fdi.seek(0, 2) # 2=end
			seekable = True
		except OSError:
			if __debug__: print("seek() failed on", arg)
	if seekable:
		assert size is not None
		if size == 0:
			return size, (head_b, tail_b)
		tail_length = min(tail_length, size)
		fdi.seek(-tail_length, 2)
		tail_b = fdi.read(tail_length)
		fdi.seek(0, 0) # 0=begin

	first_b = fdi.read(buffer_size)
	buffer_total = len(first_b)
	assert buffer_total, "Not expecting empty buffer"
	if buffer_total:
		head_b = first_b[:head_length]
		if callback: callback(first_b)
	if (buffer_total < buffer_size):
		return buffer_total, (head_b, first_b[-tail_length:])

	prev_b, this_b = first_b, fdi.read(buffer_size)
	assert len(this_b)
	while len(this_b) == buffer_size: # runs for second block ... last whole block
		if 0 < limit < buffer_total+buffer_size:
			size = -1
			tail_b = b''
			break
		buffer_total += buffer_size
		if callback: callback(this_b)
		prev_b, this_b = this_b, fdi.read(buffer_size)

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
	fdi.close()
	return buffer_total, (head_b, tail_b)


# vim: tabstop=4 shiftwidth=4 softtabstop=4 number :
