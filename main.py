from triage.loader import load_emails

for e in load_emails("data/emails.json"):
    print(e.sender, "|", e.subject)