from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools.function_tool import FunctionTool
from src.tools.profile import data_profiler
from src.utils.AgentConfig import retry_config

profiler=Agent(
    name='Profiler_Agent',
    description='Agent that proflies given data (in .csv format) using a fucntion tool',
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an expert data profiler.Don't analyze the data yourself instead use the data_profiler tool and interpret the output to create a profile. It should contain the following pionts,
    1. Column names and their inferred types (group the columns of same type).  
    2. Percentage of missing values for each column.
    3. Cardinality (number of unique values) for categorical columns.
    3. A summary of potential issues (e.g., "Column 'Sale_Amount' is an 'object' type but looks numeric. Column 'Order_Date' is an 'object' but looks like a date.").
""",
tools=[FunctionTool(func=data_profiler)],
output_key='data_profile'
)
