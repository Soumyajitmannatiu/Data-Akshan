from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from src.utils.AgentConfig import retry_config

planner=Agent(
    name='Planner_Agent',
    description='Agent expert in planning different stages of data engineering',
    model=Gemini(model="gemini-2.5-pro", retry_options=retry_config),
    instruction="""You are an expert data engineer. You will create a plan for {task} based on the user's request and task context:{task_context}.
    The plan MUST include:
    1. How the task will be handled.(Keep this part concise)
    2. Clear steps on how it should be handled.
""",
output_key='stage_plan'
)
