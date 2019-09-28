def avg(l):
	"""
	Average the values in a list
	@param l: list of floats or ints
	@type l: list[float]
	@return: average of values in list
	@rtype: float
	"""
	return sum(l) / len(l)


class SensorError(Exception):
	pass
