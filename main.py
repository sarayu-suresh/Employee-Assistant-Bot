from fastapi import FastAPI, Request
from pydantic import BaseModel
import faiss
import numpy as np
import json
import requests
from dotenv import load_dotenv
import os
from fastapi.responses import JSONResponse
import uuid
import re

from scripts.chat_auth import get_chat_access_token
from scripts.sheet_utils import get_manager_email, notify_manager_in_space
from agents.github_query import answer_from_github_repo
from scripts.cards import build_leave_confirmation_card, build_ai_email_preview_card
from models.query_llm import query_mistral_dkubex
from models.query_embedding import get_remote_embedding
from agents.detect_intent import detect_intent
from agents.query_docs import answer_from_docs
from agents.generate_response import generate_response
from agents.find_expert import find_internal_expert
from scripts.drive_utils import search_drive_folder
from scripts.sheet_utils import get_google_doc_text
from scripts.sheet_utils import get_status_doc_url, get_google_doc_text
from agents.weekly_status_analyzer import analyze_status_doc
from scripts.email_utils import fetch_recent_emails
from agents.email_taskmaster import summarize_email, extract_task, rank_and_format_tasks

load_dotenv()
app = FastAPI()

user_sessions = {}

class ChatInput(BaseModel):
    message: str

@app.post("/chat-event")
async def chat_event(request: Request):
    body = await request.json()
    event_type = body.get("type")
    message = body.get("message", {}).get("text", "").lower()
    user = body.get("user", {}).get("email", "unknown")
    space_id = body.get("space", {}).get("name")

    if event_type == "MESSAGE":
        session = user_sessions.get(user, {"state": None})
        session["space_id"] = space_id
        user_sessions[user] = session

    action = body.get("common", {}).get("invokedFunction", "")
    raw_params = body.get("common", {}).get("parameters", [])
    params = {p["key"]: p["value"] for p in raw_params} if isinstance(raw_params, list) else {}
    session = user_sessions.get(user, {"state": None})

    if event_type == "CARD_CLICKED":
        if action == "confirm_action":
            if session.get("state") == "awaiting_confirmation":
                if raw_params.get("confirmation") == "yes":
                    manager_email = get_manager_email(user)
                    if manager_email:
                        session["manager_email"] = manager_email
                        user_sessions[(user, manager_email)] = session
                        success = notify_manager_in_space(user, session["reason"], session["request_id"])
                        if success:
                            session["state"] = "submitted"
                            return JSONResponse(content={"text": "✅ Leave request sent to manager."})
                        else:
                            return JSONResponse(content={"text": "❌ Failed to notify manager."})
                    else:
                        return JSONResponse(content={"text": "❌ Manager not found."})
                else:
                    user_sessions.pop(user, None)
                    return JSONResponse(content={"text": "Leave request not submitted."})

        elif action == "approve_leave":
            employee = raw_params.get("employee")
            reason = raw_params.get("reason")
            request_id = raw_params.get("request_id")
            session_key = (employee, user, request_id)
            emp_session = user_sessions.get(session_key, {})
            emp_session["manager_email"] = user 
            if emp_session.get("action_taken"):
                return JSONResponse(content={"text": "⚠️ Already approved/rejected."})
            emp_session["action_taken"] = True
            user_sessions[session_key] = emp_session

            emp_space = user_sessions.get(employee, {}).get("space_id")
            ai_mail = generate_response(
                f"Generate a very formal leave approval email based on this reason: {reason}",
                instruction="You are a helpful assistant. Write an email that an employee would send after getting leave approval."
            )
            user_sessions[employee]["mail_content"] = ai_mail
            user_sessions[(employee, request_id)] = {
                "action_taken": False,
                "mail_content": ai_mail
            }

            token = get_chat_access_token("config/creds.json")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = build_ai_email_preview_card(employee, ai_mail, request_id)

            if not emp_space:
                return JSONResponse(content={"text": "Could not get employee DM space."})

            dm_url = f"https://chat.googleapis.com/v1/{emp_space}/messages"
            res = requests.post(dm_url, headers=headers, json=payload)
            print("DM sent to employee:", res.status_code)

            return JSONResponse(content={"text": "✅ Approved. Employee notified."})

        elif action == "reject_leave":
            employee = raw_params.get("employee")
            reason = raw_params.get("reason")
            request_id = raw_params.get("request_id")
            session_key = (employee, user, request_id)
            emp_session = user_sessions.get(session_key, {})
            if emp_session.get("action_taken"):
                return JSONResponse(content={"text": "⚠️ Already approved/rejected."})
            emp_session["action_taken"] = True
            user_sessions[session_key] = emp_session

            emp_space = user_sessions.get(employee, {}).get("space_id")
            if not emp_space:
                return JSONResponse(content={"text": "Could not get employee DM space."})

            token = get_chat_access_token("config/creds.json")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"text": "📝 Your leave request has been rejected!"}

            dm_url = f"https://chat.googleapis.com/v1/{emp_space}/messages"
            res = requests.post(dm_url, headers=headers, json=payload)
            print("Rejection DM sent:", res.status_code)

            return JSONResponse(content={"text": "✅ Rejected. Employee notified."})
        
        elif action == "send_leave_email":
            employee = body.get("user", {}).get("email")
            request_id = raw_params.get("request_id")
            print(request_id)
            session_key = (employee, request_id)
            emp_session = user_sessions.get(session_key)
            print(emp_session)

            if not emp_session:
                return JSONResponse(content={"text": "⚠️ No pending mail session found."})
            if emp_session is not None:
                if emp_session.get("action_taken"):
                    return JSONResponse(content={"text": "⚠️ You already acted on this message."})

            emp_session["action_taken"] = True
            user_sessions[session_key] = emp_session
            content = user_sessions.get(employee, {}).get("mail_content")
            if content:
                print("Send this mail:", content)

            return JSONResponse(content={"text": "✅ Mail sent."})

        elif action == "ignore_leave_email":
            employee = body.get("user", {}).get("email")
            request_id = raw_params.get("request_id")
            session_key = (employee, request_id)
            emp_session = user_sessions.get(session_key, {})
            if emp_session.get("action_taken"):
                return JSONResponse(content={"text": "⚠️ You already acted on this message."})

            emp_session["action_taken"] = True
            user_sessions[session_key] = emp_session
            return JSONResponse(content={"text": "Mail ignored."})

    if message:
        # token = get_chat_access_token("config/creds.json")
        # headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        # loading_payload = {
        #     "text": "Please wait a moment...."
        # }
        # loading_url = f"https://chat.googleapis.com/v1/{space_id}/messages"
        # loading_res = requests.post(loading_url, headers=headers, json=loading_payload)
        # print("Loading message sent:", loading_res.status_code)
        
        intent = detect_intent(message)
        print(f"Detected intent: {intent}")
        if intent == "raise_leave_request":
            request_id = str(uuid.uuid4())
            session = {"state": "awaiting_confirmation", "reason": message, "ticket_type": "Leave", "space_id": space_id, "request_id": request_id}
            user_sessions[user] = session
            return JSONResponse(content=build_leave_confirmation_card("Do you want to submit this leave request?", message))

        elif intent == "raise_hr_ticket":
            return JSONResponse(content={"text": "HR ticket flow not implemented."})
        elif intent == "raise_it_ticket":
            return JSONResponse(content={"text": "IT ticket flow not implemented."})
        elif intent == "greeting":
            response = generate_response(message, instruction="You are a friendly assistant. Greet the user.")
            return JSONResponse(content={"text": response})
        elif intent == "document_query":
            # Extract a simple keyword from the user message
            # keyword = extract_query_term(message)  # implement this to strip stopwords etc.
            doc_info = search_drive_folder(message)
            return JSONResponse(content={"text": doc_info})
        elif intent == "github_repo_query":
            repo_url_match = re.search(r"https?://github\.com/[\w\.-]+/[\w\.-]+", message)
            if repo_url_match:
                repo_url = repo_url_match.group()
                answer = answer_from_github_repo(message, repo_url)
                return JSONResponse(content={"text": answer})
        elif intent == "status_doc":
            name = generate_response(message, instruction="Extract the person name from this message, return just the name")
            print(name)
            if not name:
                return JSONResponse(content={"text": "❌ Could not extract name. Try saying 'What is the status of <name>'."})
            doc_url = get_status_doc_url(name)
            if not doc_url:
                return JSONResponse(content={"text": f"❌ Could not find a document for {name}."})
            try:
                doc_text = get_google_doc_text(doc_url)
                summary = analyze_status_doc( doc_text, question=message, person_name=name)
                return JSONResponse(content={"text": f"📄 *Status summary for {name}*:\n\n{summary}"})
            except Exception as e:
                print("Doc fetch/analyze error:", str(e))
                return JSONResponse(content={"text": f"❌ Error processing document for {name}."})

        elif intent == "emails_summarizer":
            try:
                emails = fetch_recent_emails(user,  max_emails=5)
                if not emails:
                    return JSONResponse(content={"text": "📭 No recent emails found."})

                task_responses = []
                for email in emails:
                    summary = summarize_email(email)
                    task = extract_task(summary)
                    print("Task Extracted:", task)
                    task_responses.append(task)

                final_summary = rank_and_format_tasks(task_responses)
                return JSONResponse(content={"text": final_summary})

            except Exception as e:
                print("Email summarization error:", e)
                return JSONResponse(content={"text": "⚠️ Could not analyze emails."})
        elif intent == "need_help":
            response = find_internal_expert(message)
            return JSONResponse(content={"text": response})
        else:
            answer = answer_from_docs(message)
            return JSONResponse(content={"text": answer})

    return JSONResponse(content={"text": "I'm not sure how to help with that yet."})

