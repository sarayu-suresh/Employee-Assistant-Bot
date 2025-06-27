from models.query_llm import query_mistral_dkubex

def analyze_status_doc(doc_text: str, question: str = "", person_name: str = "") -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant tasked with answering questions based on an employee's weekly status report.\n"
                "Given the employee's name, their status report text, and a user question, generate a direct, insightful, and formal response.\n"
                "Always answer based only on the status report content. If the information is missing, say 'Not mentioned in the report.'"
            )
        },
        {
            "role": "user",
            "content": f"""Employee: {person_name}
                      
          Question: {question}

          --- Status Report ---
          {doc_text.strip()}
          --- End of Report ---
          """
                  }
    ]

    return query_mistral_dkubex(messages)
