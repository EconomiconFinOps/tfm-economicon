"""Shared private admission, used only while holding the app's chat_gate."""

POLICY = "jup-035.summary-one-reserve-five.v2"


def main_active(app):
    return sum(entry["task"] is not None for entry in app.state.chat_attempts.values())


def summary_active(app):
    return sum(
        getattr(job, "admitted", False) and not getattr(job, "settled", False)
        for job in getattr(app.state, "summary_jobs", {}).values()
    )


def main_allowed(app, capacity):
    return main_active(app) + summary_active(app) < capacity


def summary_allowed(app, capacity):
    summaries = summary_active(app)
    return summaries == 0 and capacity - main_active(app) - summaries - 1 >= 5
