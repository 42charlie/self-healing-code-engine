
class LineAlignmentError(Exception):
    """Raised when the fuzzy matching engine cannot find the target line indices safely."""
    pass

def count_visible_chars(line: str) -> int:
    invisible_chars = {"\u200B", "\u200C", "\u200D", "\uFEFF", "\u00A0"}
    return sum(1 for char in line if not char.isspace() and char not in invisible_chars)

def get_correct_line_index(source_code: list,
		target_index: int,
		line_length: int,
		keywords: list) -> int:

	'''Returns the index of the line that is most likely to be the correct line based on the given keywords and line length.'''
	scores = []
	lines_range = source_code[max(0, target_index-6): min(len(source_code), target_index+5)]
	print(f"Lines range: {lines_range}, lines len: {len(lines_range)}")
	half_range = len(lines_range) // 2
	for local_index, line in enumerate(lines_range):
		score = 0
		global_index = local_index + max(0, target_index - 5)

		#calculate keywords score
		for keyword in keywords:
			if keyword in line:
				score += 25

		#calculate position score
		score += (half_range - abs(global_index - target_index)) * 5

		#calculate length score
		length_diff = abs(line_length - count_visible_chars(line))
		if line_length > 0:
			score += max(0, (1 - (length_diff / line_length))) * 30
		elif length_diff == 0:
			score += 30  # Perfect match if both are zero

		scores.append((global_index, score))
	scores.sort(key=lambda x: x[1], reverse=True)
	print(f"Scores: {scores}")

	if len(scores) == 1 and scores[0][1] > 50:
		return scores[0][0]
	if len(scores) > 1 and scores[0][1] > 50 and scores[0][1] > scores[1][1] + 10:
		return scores[0][0]

	return -1

def update_source_code(source_code: list,
					   target_index: int,
					   lines_to_remove: int,
					   line_length: int,
					   lines_to_add: list,
					   keywords: list) -> list:

	new_source_code = []
	correct_index = get_correct_line_index(source_code, target_index, line_length, keywords)
	if correct_index != -1:
		new_source_code.extend(source_code[:correct_index])
		new_source_code.extend(lines_to_add)
		new_source_code.extend(source_code[correct_index + lines_to_remove:])
	else:
		raise LineAlignmentError(
        f"Line matching failed. Target index {target_index} with keywords {keywords} "
        f"and length {line_length} could not be aligned with high confidence."
    )
	return new_source_code
