from agents.leave_request_agent import LeaveRequestAgent
from agents.greeting_agent import GreetingAgent
from agents.file_fetcher_agent import FileFetcherAgent
from agents.find_expert_agent import FindExpertAgent
from agents.policy_query_agent import PolicyQueryAgent
from agents.status_analyser_agent import StatusDocAgent
from agents.email_summariser_agent import EmailSummarizerAgent
from agents.github_agent import GithubAgent
from agents.meeting_scheduler_agent import MeetingSchedulerAgent

agents = [
    LeaveRequestAgent(),
    GreetingAgent(),
    FileFetcherAgent(),
    FindExpertAgent(),
    PolicyQueryAgent(),
    StatusDocAgent(),
    EmailSummarizerAgent(),
    GithubAgent(),
    MeetingSchedulerAgent()
]

def dispatch_agent(intent: str, message: str, user: str, session: dict) -> dict:
    for agent in agents:
        if agent.can_handle(intent):
            return agent.handle(message, user, session)
    return {"response": {"text": "🤖 Sorry, I don’t know how to handle that yet."}}
