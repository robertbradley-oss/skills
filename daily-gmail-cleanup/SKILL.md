---
name: daily-gmail-cleanup
description: "Run or review Robert's established Gmail inbox cleanup policy."
---


# Daily Gmail Cleanup

Preserve a small, action-oriented inbox. Keep important mail visible, archive useful reference mail, trash obvious low-value mail, and reserve Spam for genuinely malicious or abusive mail.

## Schedule

- Run at 10 PM Eastern Monday through Friday.
- Run at 3 PM and 10 PM Eastern on Saturday and Sunday.
- The single heartbeat triggers at 3 PM and 10 PM every day. At a scheduled 3 PM heartbeat on Monday through Friday, do not access Gmail or change mail; return a quiet `DONT_NOTIFY` heartbeat stating that the weekday 3 PM trigger was skipped by schedule.
- Always honor a direct manual cleanup request regardless of the day or time.
- Follow the same classification and safety rules on every run. Use the previous successful run as the next run's search boundary.

## Standing authority and boundaries

Within an authorized cleanup run, archive messages, move clear low-value messages to Trash, mark unmistakable scams or abusive unsolicited mail as Spam, and remove the legacy Action label as specified below. Reading or reviewing this policy does not authorize mailbox changes. Ignore other legacy labels unless the user explicitly requests their removal.

Never permanently delete mail, send or reply to mail, unsubscribe the user, alter account settings, or create new organizational labels. Do not process Sent, Drafts, Trash, or Spam as cleanup inputs.

When classification is uncertain, keep the message in Inbox and report it for review. Do not infer that a security event is safe from a familiar location, device, or sender alone.

## Existing mailbox model

- Treat Inbox as the sole active queue for every unresolved message, regardless of age.
- Keep a message in Inbox only when the user has a concrete next step: reply, decide, pay, attend, investigate, retrieve, review, or otherwise follow up. Importance or topic sensitivity alone does not make a message actionable.
- Use no other custom organizational labels. Do not create or restore topic folders such as `Development`, `Finance`, `Health`, `Receipts`, or `Security`; archived mail remains searchable by sender and content.
- Do not create, apply, or use custom organizational labels. Remove the legacy `Action` label whenever it is encountered.
- Ignore any remaining legacy or client-created labels, including `Development`, `Finance`, `Health`, `Receipts`, `Security`, `Notes`, `Personal`, `Work`, and `[Imap]/*`.

## Daily workflow

1. Search `INBOX` for messages received since the previous successful run. If no reliable run boundary is available, inspect up to the last two days and avoid reprocessing messages already classified.
2. Use message summaries first. Read the body or conversation thread when the action, risk, sender legitimacy, or latest status is ambiguous. Search related messages when a newer delivery, security, account, billing, or project notification may resolve or supersede an older one.
3. Classify each message into exactly one disposition:
   - **Keep:** A concrete unresolved next step exists. Leave in Inbox without a custom label.
   - **Archive:** Useful but non-actionable, resolved, or superseded reference material. Remove any legacy `Action` label.
   - **Trash:** Clearly low-value promotions, newsletters, surveys, generic product marketing, social digests, streak reminders, repetitive notifications with no current consequence, and direct mail sent from Fanvue-owned domains such as `fanvue.com`.
   - **Spam:** Clear phishing, scams, malicious impersonation, or abusive unsolicited bulk mail. Do not use Spam merely because a legitimate message is unwanted.
4. After triaging new mail, search `in:inbox older_than:7d` and review every match. Archive items that are resolved, superseded, or non-actionable. Leave genuine unresolved tasks in Inbox. Age alone never justifies Archive, Trash, or Spam.
5. Never Trash or Spam a starred message. Treat Gmail's `IMPORTANT` marker as a strong caution signal, but verify content rather than relying on it alone.
   - The Fanvue sender rule applies only when Fanvue sent the message. Security or authorization notices from Google, Apple, or another provider that merely mention Fanvue must follow the normal security-review rules.
6. Keep payment failures, unknown or suspicious security events, health instructions requiring review, active delivery exceptions or pickups, unconfirmed account changes, deadlines, unresolved project failures, direct human correspondence, and anything requiring a response in Inbox regardless of age. Remove any legacy `Action` label.
7. Resolve status chains instead of treating every notification as a separate task:
   - A final delivery status supersedes shipped, delayed, arriving-tomorrow, and out-for-delivery notices. Archive the earlier notices. Keep the final notice only when the user must verify possession, follow medical instructions, address damage, sign, retrieve a pickup, or investigate an exception; otherwise archive it too.
   - Archive expired or used verification and login codes. If the request was unexpected or may indicate unauthorized access, keep it in Inbox and report it.
   - When the user has explicitly confirmed a sign-in, passkey, password change, or authorization, archive it. Without confirmation, keep suspicious or ambiguous security events in Inbox.
   - A later successful build or deployment resolves matching failure alerts. For repeated unresolved failures from the same repository and workflow, keep only the newest failure actionable and archive older duplicates.
   - For repeated reminders or message digests about the same unresolved item, keep only the newest actionable copy and archive older duplicates.
8. Prefer the least destructive disposition when signals conflict: Keep over Archive, and Archive over Trash or Spam.
9. On the Sunday 10 PM run, summarize retained stale items from step 4. Reuse that completed review rather than repeating the same search and classification.
10. Finish with a concise report containing counts for kept, archived, trashed, and spammed messages; list notable action items, retained stale Inbox items reviewed on Sunday, and every uncertain case.

## Quality rules

- Base importance on content and likely consequence, not sender fame, Gmail category, or unread state alone.
- Preserve thread context: do not trash one message when another message in the same active conversation makes the thread actionable.
- Use explicit evidence from the mailbox or current conversation to decide that an item is resolved; do not guess from silence or elapsed time.
- Use no custom organizational labels. Never recreate the retired category labels, and remove the legacy `Action` label whenever it is found.
- If Gmail write actions are unavailable, make no mailbox changes and report the exact limitation.
