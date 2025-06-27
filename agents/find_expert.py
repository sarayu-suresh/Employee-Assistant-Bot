from scripts.sheet_utils import get_sheet_client
from models.query_llm import query_mistral_dkubex

def find_internal_expert(question: str) -> str:
    client = get_sheet_client()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Fxg9wKMlAPQnwXxXnGengE1c--ji_0QgjK2zor5WXBA/edit?gid=0#gid=0").sheet1
    data = sheet.get_all_records()

    context = ""
    for row in data:
        name = row.get("Employee Name", "")
        skills = row.get("Skills", "")
        projects = row.get("Projects", "")
        experience = row.get("Experience", "")
        context += f"{name} has {experience} experience and has worked on {projects}. Skills: {skills}.\n"

    prompt = f"""
You are an AI assistant. Based on the following employee data, suggest the best person who can help with the issue described.

Data:
{context}

Issue: {question}
"""
    messages = [
        {"role": "system", "content": "You are an expert recommender assistant."},
        {"role": "user", "content": prompt}
    ]
    return query_mistral_dkubex(messages)
