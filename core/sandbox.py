import re
import tempfile
import subprocess
from config.settings import VENV_SANDBOX_PATH

def execute_code(source_code: list) -> subprocess.CompletedProcess:
	''' Executes the given source code in a sandboxed environment. '''

	code = '\n'.join(source_code)

	with tempfile.TemporaryDirectory() as sandbox_dir:
		# Write the source code to a file in the sandbox directory
		with open(f'{sandbox_dir}/source_code.py', 'w') as f:
			f.write(code)

		while True:
			try:
				# Execute the code and capture the output
				result = subprocess.run([VENV_SANDBOX_PATH, f'{sandbox_dir}/source_code.py'],
							capture_output=True,
							text=True,
							timeout=5,
							cwd=sandbox_dir)
			except subprocess.TimeoutExpired as e:
				result = subprocess.CompletedProcess(args=e.cmd, returncode=1, stdout='', stderr='Execution timed out.')

			# If there's a ModuleNotFoundError, try to install the missing module
			if result.returncode != 0 and 'ModuleNotFoundError' in result.stderr:
				if not install_missing_module(result.stderr):
					break
			else:
				break

	return result

def install_missing_module(stderr: str) -> bool:
	''' Installs the missing module using pip. '''

	match = re.search(r"No module named '([^']+)'", stderr)
	if match:
		missing_module = match.group(1)
		pip_result = subprocess.run([VENV_SANDBOX_PATH, '-m', 'pip', 'install', missing_module], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		if pip_result.returncode != 0:
			return False
	else:
		return False

	return True