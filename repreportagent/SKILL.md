---
name: repreportagent
description: "Handle explicit RepReport agent requests using current repository instructions."
---


# RepReport agent

Handle a direct `/RepReportAgent` or `/repreportagent` task in `C:/Users/robby/Projects/RepReport`, unless the user names another checkout. Inspect current Git state and `AGENTS.md`; execute the requested work in the current thread.

RepReport is a local-first spreadsheet utility. Keep its product scope and output contracts in the repository, not in this launcher.

Load only the relevant repository skill under `.agents/skills/`:
- `repreport-review-parser`: review-note extraction and verified/photo/rating rules.
- `repreport-excel-export`: Review Log TSV/CSV/workbook output.
- `repreport-kpi-report`: KPI parsing and output.

Complete the requested change and relevant verification. Fix regressions caused by the change; preserve unrelated work. Follow current user direction and repository product boundaries. Commit, push, or deploy only when authorized. Report the outcome, meaningful checks, and remaining limitations concisely.
