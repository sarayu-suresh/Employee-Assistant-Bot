
import requests
import base64
import re
import json

from models.query_llm import query_mistral_dkubex

class GithubAgent:

    def can_handle(self, intent_name: str) -> bool:
        return intent_name == "github_repo_query"
    
    def handle(self, message: str, user: str, session: dict) -> dict:
        repo_url_match = re.search(r"https?://github\.com/[\w\.-]+/[\w\.-]+", message)
        if not repo_url_match:
            return {"response": {"text": "❌ Could not find a GitHub repo URL in your message."}, "session": session}
        
        repo_url = repo_url_match.group()
        owner, repo = self.extract_repo_owner_and_name(repo_url)
        if not owner or not repo:
            return {"response": {"text": "❌ Could not parse GitHub repo URL."}, "session": session}

        context = self.fetch_github_repo_context(owner, repo)
        prompt = (
            "You are a GitHub assistant. Based on the following repo content, answer the question in detail "
            "strictly from the repo content. Don't hallucinate. Provide a helpful, structured response.\n\n"
            f"{context}\n\n"
            f"Question: {message}"
        )
        messages = [
            {"role": "system", "content": "You are a GitHub code analysis assistant."},
            {"role": "user", "content": prompt}
        ]
        answer = query_mistral_dkubex(messages)

        return {"response": {"text": answer.strip() if answer else "❌ Failed to generate answer."}, "session": session}

    
    def extract_repo_owner_and_name(self,url: str):
        match = re.search(r"github\.com/([\w-]+)/([\w.-]+)", url)
        if match:
            return match.group(1), match.group(2).replace(".git", "")
        return None, None

    def fetch_github_repo_context(self, owner, repo, max_code_files=30):
        headers = {"Accept": "application/vnd.github.v3+json"}
        context_parts = []

        def fetch_readme():
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}/readme"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                    context_parts.append(f"\n📝 README:\n{content[:2000]}")
            except Exception as e:
                print("README error:", e)

        def fetch_issues():
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=5"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    for issue in resp.json():
                        if "pull_request" not in issue:
                            title = issue.get("title", "")
                            body = issue.get("body", "")[:500]
                            context_parts.append(f"\n🐞 Issue: {title}\n{body}")
            except Exception as e:
                print("Issue fetch error:", e)

        def traverse_and_collect_code(path="", collected_files=[]):
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    items = resp.json()
                    for item in items:
                        if item["type"] == "dir":
                            traverse_and_collect_code(item["path"], collected_files)
                        elif item["type"] == "file" and item["name"].endswith(('.py', '.js', '.ts', '.java')):
                            collected_files.append(item)
                            if len(collected_files) >= max_code_files:
                                return  # Stop once we hit the limit
            except Exception as e:
                print("Traversal error:", e)

        def fetch_code_files():
            collected_files = []
            traverse_and_collect_code("", collected_files)
            for file in collected_files:
                print(file)
                try:
                    file_resp = requests.get(file["download_url"], headers=headers)
                    if file_resp.status_code == 200:
                        code = file_resp.text
                        context_parts.append(f"\n📄 {file['path']}:\n{code[:1000]}")
                except Exception as e:
                    print("Code fetch error:", e)

        fetch_readme()
        fetch_issues()
        fetch_code_files()

        return "\n".join(context_parts) if context_parts else "❌ No meaningful context could be fetched."
