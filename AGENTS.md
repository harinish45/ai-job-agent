# 🤖 AI Agent Engineering Guidelines

1. **Anti-Bot & Rate-Limiting Invariants:** Never submit applications without introducing human-like variable delays (30–120s).
2. **Credential Safety:** Never log unencrypted credentials or cookies in application logs or screenshots.
3. **Database Integrity:** Always write Celery task state transitions through transaction blocks.
