# Build guide: Copilot Studio + SharePoint

Setting names in Microsoft products change often. This guide gives the sequence. Match it to whatever the screen shows today.

## 0. Get a tenant (do this first)

Copilot Studio and SharePoint need a Microsoft 365 work or school tenant. Options as of October 2026 (check each page, since these change):

- **Microsoft 365 Developer Program sandbox.** It is no longer open to everyone. Microsoft's pages say a sandbox is available to qualifying members, such as Visual Studio Professional/Enterprise subscribers and some partner programs, and the "You don't currently qualify" message is common. Docs: https://learn.microsoft.com/office/developer-program/microsoft-365-developer-program-faq
- A Microsoft community answer in July 2026 suggested the free **Power Apps Developer Plan**, a developer environment in Power Platform, Microsoft Learn temporary sandboxes, or a lab tenant from a training provider.
- **Copilot Studio trial.** I did not verify the current trial terms. Check https://www.microsoft.com/microsoft-copilot/microsoft-copilot-studio
- Do not build this in a company's production tenant. Use a personal or sandbox tenant.

If you cannot get a tenant, you can still finish steps for the Python prototype, the test set and the tracker, and clearly label the Copilot Studio part as "designed, not deployed". Do not claim results you did not measure.

## 1. SharePoint library

1. Create a SharePoint team site, e.g. "Garage Knowledge".
2. Create a document library "Maintenance Documents".
3. Upload the 10 files from `docs/docx/` (run `tools/build_docx.sh` if the folder is empty).
4. Create a SharePoint list "Unanswered Questions" with the columns in `power-automate-flow.md`.

## 2. Create the agent

1. Go to https://copilotstudio.microsoft.com and create an agent. Name: "Garage Maintenance Assistant".
2. Paste the v1 instructions from `agent-instructions-v1-baseline.md`.
3. Add knowledge: SharePoint, then the "Maintenance Documents" library URL.
4. Turn OFF general knowledge and web search so the agent can only use your documents.
5. Add 3 conversation starters: "Brake inspection interval for a tractor unit?", "I found a hydraulic leak. What now?", "How do I jump-start a truck safely?"

## 3. Wait for indexing

Newly added SharePoint files can take a while to become searchable by the agent. If the first answers say nothing was found, wait and retest before changing prompts. Note the wait in your log.

## 4. Run the baseline

1. Open the test chat in Copilot Studio. Start a new chat for each question so earlier answers do not leak in.
2. Ask the 20 questions from `test/test_questions.csv`. Copy each answer into the tracker.
3. Score each question on three things: answer correct, source correct, refusal correct (rules are on the Instructions sheet in `tracking/test-tracker.xlsx`).
4. Save as "Baseline". Do not edit the prompt until all 20 are scored.

## 4b. Optional: use Copilot Studio's built-in test sets

Copilot Studio has an agent evaluation feature where you upload test questions as a CSV and it runs them. Check whether your tenant has it. It is useful for repeats, but still read the answers yourself.

## 5. Improve, one change at a time

Use the change ideas table in `agent-instructions-v1-baseline.md`. For each version: change ONE thing, re-run all 20 questions, score, log it. Version names: v2, v3, v4.

## 6. Add the logging flow

Follow `power-automate-flow.md`, then add the instruction line it gives to the agent and run the 3 out-of-scope questions again. Check that rows appear in the SharePoint list.

## 7. Publish and demo

Publish the agent and use the demo channel or Teams, depending on what your tenant allows. Record the demo using `guides/demo-script.md`.
