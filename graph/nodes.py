from core.sandbox import execute_code
from graph.state import ChangeHistory, State
from llm_layer.client import generate_source_code, generate_code_patch, semantic_check
from core.editor import update_source_code
import re

#utils
def sanitize_error_message(stderr_content: str) -> str:
    """Strips file paths and system noise, isolating only the line number and the core exception name."""
    if not stderr_content:
        return "Unknown runtime crash."
        
    lines = [line.strip() for line in stderr_content.splitlines() if line.strip()]
    
    line_match = re.search(r"line (\d+)", stderr_content)
    line_info = f"Line {line_match.group(1)}" if line_match else "Unknown Line"
    
    core_exception = lines[-1] if lines else "RuntimeError"
    
    return f"[{line_info}] -> {core_exception}"

def queryLlm(state: State):
	'''Determines the appropriate LLM query based on the current iteration and state, and returns the response.'''
	if len(state.source_code) == 0:
		source_code = generate_source_code(state.user_request)
		return { "source_code" : source_code }
	else:
		changes_history = list(state.changes_history)
		batch_payload = generate_code_patch(state.user_request, state.source_code, state.changes_history)
		last_change = ChangeHistory(edits=batch_payload.edits)
		changes_history.append(last_change)
		return { "changes_history" : changes_history, "iteration_count": state.iteration_count + 1 }

def updateSourceCode(state: State):
	'''Applies the latest edits from the change history to the current source code and returns the updated source code.'''
	latest_change = state.changes_history[-1]
	new_source_code = update_source_code(state.source_code, latest_change.edits)
	return {"source_code": new_source_code}

def executeCode(state: State):
	'''Executes the current source code and captures any errors or exceptions that occur during execution.'''
	result = execute_code(state.source_code)
	stderr = sanitize_error_message(result.stderr)
	# print(f"Sanitized Error Message: [[{stderr}]]")
	# If this is the first iteration, we need to initialize the change history with the execution result
	if state.iteration_count == 0 and result.returncode != 0 :
		return {"changes_history": [ChangeHistory(edits=[], has_error=True, error_message=stderr)]}
	elif state.iteration_count == 0 and result.returncode == 0:
		return {"changes_history": [ChangeHistory(edits=[], has_error=False, error_message="")]}

	changes_history = state.changes_history
	if result.returncode != 0:
		changes_history[-1].has_error = True
		changes_history[-1].error_message = stderr

	return {"changes_history": changes_history}

def semanticValidator(state: State):
	'''Performs a semantic check on the current source code against the original user request and returns a structured verdict.'''
	changes_history = state.changes_history
	latest_change = changes_history[-1]
	verdict = semantic_check(state.source_code, state.user_request)
	if verdict.matches_intent == False:
		latest_change.has_error = True
		latest_change.error_message = verdict.critique
	else:
		latest_change.has_error = False
		latest_change.error_message = ""
	changes_history[-1] = latest_change
	return {"changes_history": changes_history}
