from config.settings import GENERATION_MODEL, PATCHER_MODEL, CODE_GENERATOR_PROMPT, CODE_PATCHER_PROMPT, SEMANTIC_CHECKER_PROMPT
from groq import Groq
from .schemas import BatchEditBlock, SemanticReview
import dotenv
import os

dotenv.load_dotenv()
client = Groq(api_key = os.getenv("GROQ_API_KEY"))

def generate_source_code(user_request: str) -> list:
	user_prompt = (
        f"Task Goal:\n{user_request}\n\n"
        f"Reminder: Write complete, functional code. No markdown formatting. No talking."
    )
	try:
		response = client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": CODE_GENERATOR_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
		return response.choices[0].message.content
	except Exception as e:
		return str(e)

def generate_code_patch(user_request: str, source_code: str, changes_history: list):
	user_prompt = (
        f"### ORIGINAL GOAL REQUIREMENT:\n{user_request}\n\n"
        f"### CURRENT CODEBASE STATE (WITH LINE INDICES):\n```python\n{source_code}\n```\n\n"
        f"### EXECUTION FAILURE METADATA:\n{changes_history[-3:]}\n\n"
        f"Generate the exact structured batch edits payload required to resolve this failure."
    )
	pydantic_json_schema = BatchEditBlock.model_json_schema()
	
	tools = [
        {
            "type": "function",
            "function": {
                "name": "submit_code_patches",
                "description": "Submits a batch of non-contiguous code edits to fix an existing file.",
                "parameters": pydantic_json_schema
            }
        }
    ]
	try:
		response = client.chat.completions.create(
            model=PATCHER_MODEL,
            messages=[
                {"role": "system", "content": CODE_PATCHER_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
			tools=tools,
        	# force Groq to execute this specific function call block
        	tool_choice={"type": "function", "function": {"name": "submit_code_patches"}},
        )
		# extract the structured tool arguments string from the response payload
		tool_call = response.choices[0].message.tool_calls[0]
		raw_arguments_json = tool_call.function.arguments
		
		# hydrate the raw string directly back into your strict Pydantic instance
		parsed_payload = BatchEditBlock.model_validate_json(raw_arguments_json)
		return parsed_payload
	except Exception as e:
		return str(e)

def semantic_check(source_code:str, user_request: str):
	user_prompt = (
        f"### ORIGINAL USER REQUIREMENT:\n{user_request}\n\n"
        f"### EXECUTING SOURCE CODE:\n```python\n{source_code}\n```\n\n"
        f"Evaluate the code against the requirement and return your structured verdict."
    )
	schemaDict = SemanticReview.model_json_schema()
	schemaDict['additionalProperties'] = False
	try:
		response = client.chat.completions.create(
            model=PATCHER_MODEL,
            messages=[
                {"role": "system", "content": SEMANTIC_CHECKER_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
			response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "semantic_review_schema",
                    "strict": True,
                    "schema": schemaDict
                }
            }
        )
		return SemanticReview.model_validate_json(response.choices[0].message.content)
	except Exception as e:
		return SemanticReview(
            matches_intent=False, 
            critique=f"The Semantic checker crashed internally: {str(e)}"
        )