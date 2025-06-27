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
