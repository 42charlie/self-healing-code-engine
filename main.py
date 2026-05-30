from graph.workflow import graph

initial_state = {
    "user_request": "Write a Python function that calculates the factorial of a number.",
    "source_code": [],
    "changes_history": [],
    "iteration_count": 0
}

print("--- Running Graph ---")
for step in graph.stream(
    initial_state,
):
    print(f"Step: {step}")