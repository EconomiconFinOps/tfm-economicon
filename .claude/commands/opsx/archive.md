---
name: "OPSX: Archive"
description: Archive a completed change in the experimental workflow
category: Workflow
tags: [workflow, archive, experimental]
---

Archive a completed change in the experimental workflow.

**Input**: Optionally specify a change name after `/opsx:archive` (e.g., `/opsx:archive add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show only active changes (not already archived).
   Include the schema used for each change if available.

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check artifact completion status**

   Run `openspec status --change "<name>" --json` to check artifact completion.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context
   - `artifacts`: List of artifacts with their status (`done` or other)

   If status reports `actionContext.mode: "workspace-planning"`, explain that workspace archive is not supported in this slice and STOP. Do not move workspace changes into repo-local archives or edit linked repos.

   **If any artifacts are not `done`:**
   - Display warning listing incomplete artifacts
   - Prompt user for confirmation to continue
   - Proceed if user confirms

3. **Check task completion status**

   Read the tasks file (typically `tasks.md`) to check for incomplete tasks.

   Count tasks marked with `- [ ]` (incomplete) vs `- [x]` (complete).

   **If incomplete tasks found:**
   - Display warning showing count of incomplete tasks
   - Prompt user for confirmation to continue
   - Proceed if user confirms

   **If no tasks file exists:** Proceed without task-related warning.

4. **Assess delta spec sync state**

   Use `artifactPaths.specs.existingOutputPaths` from status JSON to check for delta specs. If none exist, proceed without sync prompt.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `openspec/specs/<capability>/spec.md`
   - Determine what changes would be applied (adds, modifications, removals, renames)
   - Show a combined summary before prompting

   **Prompt options:**
   - If changes needed: "Sync now (recommended)", "Archive without syncing"
   - If already synced: "Archive now", "Sync anyway", "Cancel"

   If user chooses sync, use Task tool (subagent_type: "general-purpose", prompt: "Use Skill tool to invoke openspec-sync-specs for change '<name>'. Delta spec analysis: <include the analyzed delta spec summary>"). Proceed to archive regardless of choice.

5. **Check architecture decision records**

   Before archive, read `design.md` and `review.md` for ADR references or `ADR not applicable`.

   If the change includes a durable/cross-cutting architecture decision and no ADR is linked, STOP before archive and ask for the ADR to be created or linked. Accepted architecture decisions must be reflected in Git/OpenSpec/ADR, not only in Engram.

6. **Run the project HU harness gate**

   Before moving the change to archive, run:
   ```bash
   pnpm hu:check -- --change "<name>"
   ```

   If it fails, STOP before archive. Fix the missing approval, open task, review finding, spec validation, or anti-harness issue first. Document harness failures or workarounds in `review.md`; unresolved, deferred, or out-of-scope harness issues also go to `openspec/findings/backlog.md`.

7. **Perform the archive**

   Create an `archive` directory under `planningHome.changesDir` if it doesn't exist:
   ```bash
   mkdir -p "<planningHome.changesDir>/archive"
   ```

   Generate target name using current date: `YYYY-MM-DD-<change-name>`

   **Check if target already exists:**
   - If yes: Fail with error, suggest renaming existing archive or using different date
   - If no: Move `changeRoot` to the archive directory

   ```bash
   mv "<changeRoot>" "<planningHome.changesDir>/archive/YYYY-MM-DD-<name>"
   ```

8. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Spec sync status (synced / sync skipped / no delta specs)
   - Note about any warnings (incomplete artifacts/tasks)

9. **Run post-archive documentation review**

   After the archive move succeeds, use the Skill tool to invoke `openspec-doc-reviewer` for the archived path.

   The reviewer should:
   - compare the archived artifacts with live documentation
   - update `docs/architecture.md`, app READMEs, or manuals when clear drift exists
   - update `docs/hu-release-notes.md` with one short release note, the HU review link, and ADR links when present
   - suggest an ADR when the completed change introduced a durable architecture decision
   - avoid product code, archived artifacts, and OpenSpec spec edits unless explicitly requested

   Include the doc review summary in the archive result. If the doc review cannot run, do not undo the archive; report the blocker and the exact reviewer command/request the user should run next.

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** Synced to main specs
**Docs:** post-archive doc review and HU release note completed (or "needs follow-up: <reason>")

All artifacts complete. All tasks complete.
```

**Output On Success (No Delta Specs)**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** No delta specs
**Docs:** post-archive doc review and HU release note completed (or "needs follow-up: <reason>")

All artifacts complete. All tasks complete.
```

**Output On Success With Warnings**

```
## Archive Complete (with warnings)

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/
**Specs:** Sync skipped (user chose to skip)
**Docs:** post-archive doc review and HU release note completed (or "needs follow-up: <reason>")

**Warnings:**
- Archived with 2 incomplete artifacts
- Archived with 3 incomplete tasks
- Delta spec sync was skipped (user chose to skip)

Review the archive if this was not intentional.
```

**Output On Error (Archive Exists)**

```
## Archive Failed

**Change:** <change-name>
**Target:** the archive path derived from `planningHome.changesDir`/YYYY-MM-DD-<name>/

Target archive directory already exists.

**Options:**
1. Rename the existing archive
2. Delete the existing archive if it's a duplicate
3. Wait until a different date to archive
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Do not archive before `pnpm hu:check -- --change <name>` passes
- Do not archive a change with durable architecture decisions unless its ADR is created/linked or review marks ADR not applicable
- Don't block archive on warnings - just inform and confirm
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- Run `openspec-doc-reviewer` immediately after a successful archive and include its result in the final summary
- If sync is requested, use the Skill tool to invoke `openspec-sync-specs` (agent-driven)
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
