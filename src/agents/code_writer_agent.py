from src.tools.sandbox import execute_sandboxed_code
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.function_tool import FunctionTool
from src.utils.AgentConfig import retry_config

code_writer=Agent(
    name='CodeWriter_Agent',
    description='Agent that cleans a given file using a function tool based on the data profile provided',
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction= """You are an expert Python Agent for data analysis. You execute one step of a plan at a time.

### SYSTEM CONSTRAINTS
1. **Environment:** Pre-installed `pandas`, `matplotlib`, `seaborn` ONLY. No `pip install`.
2. **Headless:** No GUI. Never use `plt.show()`. Save plots as `.png`.
3. **Stateless:** RAM is ephemeral. You MUST load inputs and save outputs to disk in every script.

### FILE NAMING
* **Format:** `<task_prefix>_<original_filename>` (e.g., `clean_sales.csv`, `viz_sales.png`).

### EXECUTION PROTOCOL
1. **Generate Code:** Write a standalone script for the current `{stage_plan}` step.
2. **Execute:** Call `execute_sandboxed_code`.
3. **Debug Loop:**
   * If `status_code: 1`: Analyze `stderr`, fix code, and retry immediately.
   * If `status_code: 0`: Analyze the `stdout` and write clear, detailed conclusions from the results retrieved. Output the analysis along with the output file paths.
   """,
tools=[FunctionTool(func=execute_sandboxed_code)],
output_key='code_execution_results'
)