from datetime import datetime
import json
import requests

from scripts.chat_auth import get_chat_access_token

def build_leave_confirmation_card(title, message=None):
    return {
        "cards": [
            {
                "header": {"title": title, "subtitle": message or "Please confirm your action."},
                "sections": [
                    {
                        "widgets": [
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Yes",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "confirm_action",
                                                    "parameters": [{"key": "confirmation", "value": "yes"}]
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "textButton": {
                                            "text": "No",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "confirm_action",
                                                    "parameters": [{"key": "confirmation", "value": "no"}]
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "textButton": {
                                            "text": "Edit",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "edit_reason",
                                                    "parameters": [{"key": "edit", "value": "true"}]
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

 
# Build a Google Chat card with @mention for manager   
def build_leave_approval_card(employee_email: str, reason: str, manager_email: str, request_id: str):
    return {
        "cards": [
            {
                "header": {
                    "title": "Leave Request",
                    "subtitle": f"From: {employee_email}"
                },
                "sections": [
                    {
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": f"<b>Reason:</b> {reason}<br><b>Action Required:</b> @{manager_email}"
                                }
                            }
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Approve",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "approve_leave",
                                                    "parameters": [
                                                        {"key": "employee", "value": employee_email},
                                                        {"key": "reason", "value": reason},
                                                        {"key": "request_id", "value": request_id}
                                                    ]
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "textButton": {
                                            "text": "Reject",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "reject_leave",
                                                    "parameters": [
                                                        {"key": "employee", "value": employee_email},
                                                        {"key": "reason", "value": reason},
                                                        {"key": "request_id", "value": request_id}
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

def build_ai_email_preview_card(employee_email: str, email_body: str, request_id: str):
    return {
        "cards": [
            {
                "header": {
                    "title": "📧 Leave Mail Preview",
                    "subtitle": "Here's the email you can send"
                },
                "sections": [
                    {
                        "widgets": [
                            {"textParagraph": {"text": email_body}}
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Send Mail",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "send_leave_email",
                                                    "parameters": [
                                                        {"key": "employee", "value": employee_email},
                                                        {"key": "request_id", "value": request_id}
                                                    ]
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "textButton": {
                                            "text": "Ignore",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "ignore_leave_email",
                                                    "parameters": [
                                                        {"key": "employee", "value": employee_email},
                                                        {"key": "request_id", "value": request_id}
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
def build_meeting_slot_selection_card(employee_email: str, participants: list, date: datetime, available_slots: list, title: str, request_id: str):
    """
    Show available slots as buttons. Clicking one triggers meeting creation.
    """
    slot_buttons = []
    for slot in available_slots[:10]: 
        slot_buttons.append({
            "textButton": {
                "text": slot,
                "onClick": {
                    "action": {
                        "actionMethodName": "confirm_meeting_slot",
                        "parameters": [
                            {"key": "employee", "value": employee_email},
                            {"key": "slot", "value": slot},
                            {"key": "participants", "value": ",".join(participants)},
                            {"key": "date", "value": date},
                            {"key": "title", "value": title},
                            {"key": "request_id", "value": request_id}
                        ]
                    }
                }
            }
        })

    return {
        "cards": [
            {
                "header": {
                    "title": f"📅 Select Meeting Slot - {date}",
                    "subtitle": f"Available options for: {title or 'Meeting'}"
                },
                "sections": [
                    {
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": f"Participants: {', '.join(participants)}"
                                }
                            }
                        ]
                    },
                    {
                        "widgets": [
                            {
                                "buttons": slot_buttons
                            }
                        ]
                    }
                ]
            }
        ]
    }

def send_loading_card(space_id: str) -> str:
    token = get_chat_access_token("config/creds.json")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "cardsV2": [
            {
                "cardId": "loadingCard",
                "card": {
                    "header": {"title": "🤖 Generating response..."},
                    "sections": [
                        {
                            "widgets": [{"textParagraph": {"text": "Thinking...⏳"}}]
                        }
                    ]
                }
            }
        ]
    }
    url = f"https://chat.googleapis.com/v1/{space_id}/messages"
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        return res.json().get("name")  
    return None
