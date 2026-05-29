from pydantic import BaseModel, Field

class SingleEditBlock(BaseModel):
	'''Represents a single code edit operation, including the location and content of the edit.'''
	target_index: int
	line_length: int
	lines_to_remove: int
	lines_to_add: list[str]
	keywords: tuple[str, str]

class BatchEditBlock(BaseModel):
	'''Represents a batch of related changes to address a specific issue.'''
	edits: list[SingleEditBlock]
	# has_error: bool
	# error_message: str | None

class SemanticReview(BaseModel):
    """The analytical verdict of the code's logical alignment with user requirements."""
    matches_intent: bool
    critique: str