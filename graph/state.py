from pydantic import BaseModel
from llm_layer.schemas import SingleEditBlock

class ChangeHistory(BaseModel):
	edits: list[SingleEditBlock]
	has_error: bool = False
	error_message: str = ""

class State(BaseModel):
	user_request: str
	source_code: list[str]
	changes_history: list[ChangeHistory] = []
	iteration_count: int = 0
