import os
import json
import logging
import requests

logger = logging.getLogger("engine.alerting")

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

def send_alert(title, message, severity="warning"):
    """
    Send an alert. If SLACK_WEBHOOK_URL is set, posts to Slack.
    Otherwise, just logs to console.
    """
    full_message = f"[{severity.upper()}] {title}: {message}"
    
    if severity == "error":
        logger.error(full_message)
    else:
        logger.warning(full_message)
    
    if SLACK_WEBHOOK_URL:
        try:
            color = {"info": "#36a64f", "warning": "#f2c744", "error": "#e74c3c"}.get(severity, "#cccccc")
            payload = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": "MedMarket Global Pipeline Monitor"
                }]
            }
            resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Alert sent to Slack")
            else:
                logger.warning(f"Slack returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Could not send Slack alert: {e}")
    else:
        logger.info("(Slack not configured — alert logged to console only)")


def alert_on_failure(dag_name, job_name, error):
    """Convenience function for pipeline failure alerts."""
    send_alert(
        title=f"Pipeline Failure: {dag_name}",
        message=f"Job `{job_name}` failed: {error}",
        severity="error"
    )


def alert_on_success(dag_name, total_jobs, duration_seconds):
    """Convenience function for pipeline success alerts."""
    send_alert(
        title=f"Pipeline Complete: {dag_name}",
        message=f"All {total_jobs} jobs succeeded in {duration_seconds:.1f}s",
        severity="info"
    )
