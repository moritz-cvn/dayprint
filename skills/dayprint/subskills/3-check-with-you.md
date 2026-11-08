# 3 · How they work

Goal: a `working_model` in `findings.json` that every later step must respect. Build it from the data first. Ask the person only what the data cannot show, and only in general terms.

## Infer first

From `day.json` and the findings, write:

- `tempo`: `fast`, `steady` or `slow`, and a one-line `summary`. Decide it from the numbers, not from a question:
  - **fast**: many messages a day (dozens or more), most of them short decisions, a median answer within a few minutes, and a high `blocking_share` (agents sat idle until the answer came);
  - **steady**: a daily or weekly rhythm, answers within hours, work rarely waiting on them;
  - **slow**: occasional use, long gaps.
- `facts`: three to six measured facts with their source ("90% of your answers came while an agent was waiting for them", "your day starts around 10:55 and ends after midnight on most days").
- `hypotheses`: what follows from the facts, each with `status: "inferred"`. Examples of what can be inferred and must not be asked: whether their decisions block agents (`blocking_share`), whether speed matters more than interruptions (fast answers to waiting agents), when they work, how much runs in parallel.

`must_not_slow` follows from the data too: anything with a high blocking share, anything they answer within minutes, anything on a deadline.

## Ask only what data cannot show

Some things only the person knows: what they enjoy and want to keep, what is off limits, what feels like a burden. Ask at most three questions, all optional, in one message, in their language, and keep them general. Never ask about a specific solution, never ask the person to approve a proposal at this step, and never ask what a number already answers.

Good questions:
- "Is there anything in your work you want to keep doing yourself, even if an agent could do it?"
- "Anything that is off limits for agents, such as money, customers or certain accounts?"
- "What would you happily never do again?"

Bad questions: "Should approvals happen twice a day?" (a solution), "Do your approvals block agents?" (the data answers it), anything about their particular tools or rules.

If they skip, keep the inferred model and move on; the report says what was inferred and what was confirmed.

## Record

Inferred hypotheses keep `status: "inferred"`. Answers from the person go in as `confirmed`, `corrected` (with their `answer`) or `rejected`, and fill `glad_to_hand_off`, `off_limits` and, if they name something, `must_not_slow`.

Then go to [4-map.md](4-map.md). Every design choice there has to respect `must_not_slow` and `off_limits`.
