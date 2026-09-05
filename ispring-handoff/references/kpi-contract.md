# iSpring KPI Contract

## Required weekly output

```text
KPI Summary:
Top 3 Achievements:
1.
2.
3.
Best Tickets:
Ticket #
Ticket #
Ticket #
Worst Tickets:
Ticket # — reason
Ticket # — reason
Ticket # — reason
```

## Classification rules

### Worst Ticket candidate

Include a ticket only when the chat supports at least one of these conditions:

- messy or unusually confusing handling;
- escalation or a credible escalation risk;
- conflicting, repeated, or mishandled troubleshooting;
- an unusually frustrated interaction;
- an avoidable process failure or recovery from one.

Describe the work issue, not the customer. Use neutral wording such as `Repeated troubleshooting produced conflicting guidance before escalation.`

### Best Ticket candidate

Include a ticket only when the evidence shows unusually strong handling or outcome, such as resolving a complex issue, recovering a difficult interaction, preventing escalation, or producing a notably clear and reusable solution. Routine warranty registrations and ordinary replies are not automatically Best Tickets.

### Achievement candidate

Use a concise outcome supported by one or more tickets. Prefer meaningful results over activity counts. If the outcome is not yet known, keep it uncertain.

## Evidence and lifecycle

- `Candidate` means supported enough to retain but not chosen for the final weekly report.
- `Confirmed` means the user or existing weekly chat explicitly selected it.
- `Uncertain` means relevant text is missing, truncated, contradictory, or the outcome remains open.
- Later evidence may strengthen, weaken, or remove a candidate; preserve the reason for any material change in the next summary.
- Do not choose the final three in any category until the user requests the weekly KPI report or explicitly confirms selections.

## Deduplication

- Key entries by the displayed ticket number.
- Treat URL parameters and internal support IDs as non-authoritative.
- Merge repeated appearances of the same ticket across continuation chats.
- Prefer the latest supported status while retaining earlier facts needed to explain why it qualifies.

## Privacy boundary

Transfer only:

- displayed ticket number;
- KPI category and candidate state;
- concise work-related reason;
- resolution or escalation status when supported;
- week/date range and source chat titles.

Never transfer customer identity or contact details, addresses, order information, IP addresses, attachments, full message text, or support URLs.
