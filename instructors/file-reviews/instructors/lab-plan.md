# Review — `instructors/lab-plan.md`

**Date:** 2026-03-11
**Convention files used:** [`contributing/conventions/writing/lab-plan.md`](../../../contributing/conventions/writing/lab-plan.md)

---

## Lab plan findings

### D1. Learning outcome quality

No issues found.

### D2. Bloom's taxonomy coverage

No issues found.

### D3. Lab story coherence

No issues found.

### D4. Task sequencing and dependencies

No issues found.

### D5. Acceptance criteria quality

No issues found.

### D6. Outcome-to-task alignment

No issues found.

### D7. Structural compliance

No issues found.

### D8. Practical feasibility

1. ~~**[Medium]** — [Task 3](../../lab-plan.md#task-3--implement-the-agentic-loop), lines 67–79. The task requires calling an LLM API, but the plan does not mention how students will access it (provided API key, free-tier service, locally-running model). If a paid account is needed, this conflicts with the "no paid accounts" principle (convention Section 9.8). **Suggested fix:** Add a note in the lab story or Task 3 summary specifying how the LLM is provisioned (e.g., "a local Ollama instance included in the Docker Compose file" or "an API key provided via the course portal").~~

### D9. Student experience level fit

1. **[Low]** — [Task 3](../../lab-plan.md#task-3--implement-the-agentic-loop), lines 67–79. Task 3 assumes familiarity with LLM tool-calling schemas and message-history accumulation, but neither Task 1 nor Task 2 introduces these concepts. The seed project provides scaffolding, which helps, but a student with no prior LLM experience may still find the jump from CLI building to agentic-loop implementation steep. **Suggested fix:** Add a sentence in the Task 3 summary noting that the wiki or task file will introduce the tool-calling concept before asking students to implement it, or add a [Remember]/[Understand] outcome specifically about tool-calling mechanics.

---

## TODOs

No TODOs found.

## Empty sections

No empty sections found.

---

## Summary

| Category | Count |
|---|---|
| Lab plan [High] | 0 |
| Lab plan [Medium] | 0 |
| Lab plan [Low] | 1 |
| TODOs | 0 |
| Empty sections | 0 |
| **Total** | **1** |

**Overall:** The lab plan is well-structured with clear learning outcomes, proper Bloom's taxonomy coverage, a coherent workplace narrative, and well-sequenced tasks that build naturally from exploration through implementation to agentic reasoning. The one remaining finding notes a potential cognitive jump into LLM tool-calling without prior introduction (D9).
