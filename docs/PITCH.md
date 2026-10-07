# ReplyDesk: how I explain it

*Draft from Phase 1. Numbers and the user feedback get added at the end.*

## 30 seconds

ReplyDesk is a support inbox for a small online electronics store. When a customer message comes in, four small AI agents sort it, pull out the order details, draft a reply, and check that draft against the store's rules. Then a support person sees the message and the draft side by side and approves, edits or rejects it. Nothing is sent without a human click. In one line: it reads customer messages, does the boring part, and leaves the final decision to a person.

## 2 minutes

Small support teams spend most of their day on repetitive work: reading a message, working out what it's about, finding the order ID, and typing a reply they've typed a hundred times. The urgent messages, like a power bank that's swelling or a customer who was charged twice, get buried among the routine ones.

ReplyDesk takes over that first part. Each message goes through four agents I built on Lyzr Agent Studio, each with one job. The Sorter gives a category and an urgency. The Extractor pulls out the customer name, order ID, product and request, and leaves a field empty rather than guessing. The Drafter writes a short reply that follows the store's guidelines, and asks for the order ID if it's missing. The Checker reads the draft and flags problems, like promising a refund or inventing a policy.

I used four small agents instead of one big one so that when something goes wrong I can see exactly which step failed. All the control logic lives in plain Python, not in the agents: the order of steps, saving to the database, and validating that each agent returned JSON in the right shape. If the shape is wrong, the code retries once, and then moves the message to a "needs manual handling" queue instead of crashing.

A human approves every reply, and every edit is saved, so I can measure how often drafts are good enough to send unchanged. I also built an evaluation script that runs 60 labelled messages through the real pipeline and measures accuracy, including whether the agents resist messages that try to give them instructions.

## Architecture in 5 sentences

1. A Next.js front end lets support staff log in, see the inbox, and review each ticket, and lets anyone submit a message as a customer.
2. A FastAPI back end stores tickets in PostgreSQL and, when a new ticket arrives, runs the pipeline as a background task so the request returns immediately.
3. The pipeline is plain Python that calls four Lyzr agents in order (sort, extract, draft, check) and saves each result before starting the next step, so a failure halfway keeps the work already done.
4. Every agent call goes through one client file and is validated against a Pydantic model; bad output is retried once, then the ticket goes to a manual queue, and every call is logged in an audit table.
5. Staff decisions (approve, edit, reject) are saved alongside the draft, which feeds a stats page and an evaluation script that measures the agents on 60 labelled messages.
