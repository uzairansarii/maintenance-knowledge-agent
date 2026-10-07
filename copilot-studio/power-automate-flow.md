# Power Automate flow: log unanswered questions

Goal: when the agent cannot answer, it adds a row to a SharePoint list so a person can add the missing document later.

## SharePoint list: "Unanswered Questions"

| Column | Type | Notes |
|---|---|---|
| Title | Single line of text | The user's question (rename the default column label to "Question") |
| Reason | Single line of text | e.g. "No matching document" |
| Status | Choice | New (default), Reviewed, Document added, Dismissed |
| LoggedOn | Date and time | Set by the flow |
| ReviewedBy | Person | Filled by a human |
| Resolution | Multiple lines of text | What was done |

## Flow

Name: "Log unanswered question". Build it from inside Copilot Studio (Tools, Add a tool, New agent flow) or in Power Automate. Names of triggers differ by version.

1. **Trigger:** the Copilot Studio / agent trigger ("When an agent calls the flow"). Add two text inputs: `Question` and `Reason`.
2. **Action:** SharePoint "Create item". Site: your Garage Knowledge site. List: Unanswered Questions.
   - Title = `Question`
   - Reason = `Reason`
   - Status = `New`
   - LoggedOn = `utcNow()`
3. **Return:** respond to the agent with a text output `Result` = "Logged".

## Wire it to the agent

1. Add the flow as a tool for the agent. Give it this description: "Use this when the user's question cannot be answered from the maintenance documents. Pass the user's question and a short reason."
2. Add this to the agent instructions (this becomes version v-next in your change log):

   `If you cannot answer from the documents, give the refusal sentence and then call the "Log unanswered question" tool with the user's question.`

3. Test with Q18 to Q20. Each should add one row. Check that answerable questions do NOT add rows.

## Privacy note

Questions can contain names or vehicle IDs. Keep the list restricted to the maintenance team.
