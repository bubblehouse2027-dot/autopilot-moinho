"""
Single entry point. GitHub Actions calls:
  python run.py daily     -> publish, Google posts, reviews, holiday hours
  python run.py monthly   -> monthly report
  python run.py print     -> review kit PDFs + link page (one-off, run when onboarding)
Each module only runs if it is switched on in client.yaml.
"""
import sys
import traceback

from modules.common import enabled

JOBS = {
    "daily": [("publish_meta", "modules.publish_meta"),
              ("google_posts", "modules.google_posts"),
              ("review_replies", "modules.reviews"),     # also handles review_to_post
              ("review_to_post", "modules.reviews"),
              ("holiday_hours", "modules.holiday_hours")],
    "monthly": [("monthly_report", "modules.report")],
    "print": [("review_kit", "modules.review_card"),
              ("link_page", "modules.link_page")],
}
ALWAYS = {"review_kit"}

if __name__ == "__main__":
    job = sys.argv[1] if len(sys.argv) > 1 else "daily"
    ran, failed = set(), False
    for flag, mod in JOBS[job]:
        if mod in ran or not (flag in ALWAYS or enabled(flag)):
            continue
        ran.add(mod)
        print(f"--- {mod}")
        try:
            __import__(mod, fromlist=["run"]).run()
        except Exception:                 # one broken module never stops the others
            traceback.print_exc()
            failed = True
    sys.exit(1 if failed else 0)          # red X in GitHub = something to look at
