from langgraph.graph import START, END, StateGraph

from graph.nodes import queryLlm, updateSourceCode, executeCode, semanticValidator
from graph.state import State
from typing import Literal

def generation_gate(state: State) -> Literal["executeCode", "updateSourceCode"]:
	'''Determines whether to execute the newly generated source code or to apply updates to the existing code'''
	if state.iteration_count == 0:
		return "executeCode"
	else:
		return "updateSourceCode"

def sandbox_gate(state: State) -> Literal["queryLlm", "semanticValidator", "__end__"] :
	'''Determines whether to query the LLM for a new solution or to perform a semantic validation'''
	latest_change = state.changes_history[-1]
	if latest_change.has_error:
		if state.iteration_count > 5:
			return END
		return "queryLlm"
	else:
		return "semanticValidator"

def semantic_gate(state: State) -> Literal["queryLlm", "__end__"]:
	'''Determines whether to query the LLM for a new solution or to execute the current code based on the semantic check verdict'''
	latest_change = state.changes_history[-1]
	if latest_change.has_error and state.iteration_count <= 5:
		return "queryLlm"
	else:
		return END

builder = StateGraph(State, debug=True)

builder.add_node("queryLlm", queryLlm)
builder.add_node("updateSourceCode", updateSourceCode)
builder.add_node("executeCode", executeCode)
builder.add_node("semanticValidator", semanticValidator)

builder.add_edge(START, "queryLlm")
builder.add_conditional_edges("queryLlm", generation_gate)
builder.add_edge("updateSourceCode", "executeCode")
builder.add_conditional_edges("executeCode", sandbox_gate)
builder.add_conditional_edges("semanticValidator", semantic_gate)

graph = builder.compile()