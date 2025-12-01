from google.adk.tools.tool_context import ToolContext
from google.adk.sessions.base_session_service import BaseSessionService

def add_context_variable(task:str,
                 tool_context:ToolContext):
    """
    Adds/updates context variables to the session.
    Args,
        task: The type of task that needs to be done next.
    """
    tool_context.state['task']=task
    tool_context.state['task_context']=tool_context.state.get('data_profile','No profile found')+"\n"+tool_context.state.get('stage_plan','No plan found')

def add_user_intent(user_intent:str,tool_context:ToolContext):
    """
    Adds the user's intention of analysis to the session.
    Args,
        user_intent: The user's the user's intention of analysis on the data.        
    """
    tool_context.state['user_intent']=user_intent