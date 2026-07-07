import subprocess
import os
from engine.job import Job

class AgentJob(Job):
    """
    Runs the AI agent for scheduled tasks like daily summaries.
    """

    def __init__(self, name, question, max_retries=1):
        super().__init__(name, max_retries=max_retries)
        self.question = question
        self.project_dir = os.environ.get(
            "PROJECT_DIR",
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

    def run(self):
        self.logger.info(f"Running agent query: {self.question}")

        script = f"""
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from agent.chat import validate_sql, execute_query, format_results, summarize_results, SYSTEM_PROMPT
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    system=SYSTEM_PROMPT,
    messages=[{{"role": "user", "content": "{self.question}"}}]
)
sql = response.content[0].text.strip()
print(f"SQL: {{sql}}")

is_safe, reason = validate_sql(sql)
if not is_safe:
    print(f"Safety check failed: {{reason}}")
    sys.exit(1)

columns, rows, error = execute_query(sql)
if error:
    print(f"Query error: {{error}}")
    sys.exit(1)

print(format_results(columns, rows[:20]))
summary = summarize_results(client, "{self.question}", sql, columns, rows)
print(f"Summary: {{summary}}")
"""

        result = subprocess.run(
            ["python", "-c", script],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self.logger.info(f"  [agent] {line}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"Agent query failed: {error_msg}")

        return True
