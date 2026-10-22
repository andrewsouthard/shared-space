---
name: Shared Space
slug: shared-space
status: active
created: 2026-10-22
updated: 2026-10-22
tags: [shared-space, browse, hub, projects]
---
# Shared Space

## What it is
The browsable project hub Andrew uses so conversations and assets don't get
buried in chat threads. The unit is the project, not the conversation — chats
file into project spaces. A phone-friendly page served over HTTP on the Pi.

## Where things live
- Hub URL: http://192.168.1.64:8800/
- Repo: `~/repos/shared-space` (GitHub: andrewsouthard/shared-space)
- Source of truth: `~/repos/shared-space/<project>/project.md` per project
- Generator: `~/repos/shared-space/generate.py`
- Skill: `project-spaces` (the "when to create a space" heuristic)
- Server: systemd user service `conv-dashboard.service` (port 8800, ufw LAN-only)
- Digest: cron `conv-daily-digest.py` (daily 08:00, posts recap to Discord)

## Conversations
- 2026-10-22 — Andrew: "I struggle using you... no way to easily visualize and keep track of conversations." Initial build was a timeline; Andrew clarified the real need is a browsable **project hub**, not a search/timeline. Refocused build around project spaces + a tinkerable skill.

## Decisions
- The **project** is the primary unit, not the conversation.
- Browsing by topic first; search is a fallback, not the design.
- Phone-friendly served HTML; LAN-only for now (can expose via Cloudflare later).
- Andrew controls when things get filed: a skill encodes the heuristic, tinkerable and disableable.

## Open threads
- [ ] Confirm hub renders/loads on Andrew's phone now that ufw allows port 8800
- [ ] Possibly expose outward via Cloudflare (Andrew to decide if he wants away-from-home access)

## Log
- 2026-10-22 — Built skill `project-spaces`, hub generator, repointed systemd service + ufw rule to serve shared-space on 8800.