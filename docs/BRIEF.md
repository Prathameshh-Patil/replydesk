# ReplyDesk: project brief

## The business

**Pixel & Plug** (fictional) is a small Indian online store selling consumer electronics: phones, earbuds, headphones, chargers, power banks, laptops, tablets and smartwatches. It ships across India, accepts UPI, cards, EMI and cash on delivery, and has a support team of three people who answer customer emails.

## Who uses ReplyDesk

- **Support staff** (the 3-person team) log in, read each customer message next to an AI-drafted reply, and approve, edit or reject it.
- **Customers** never see ReplyDesk. They send a message; they get a reply that a human approved.

## The problem

The team gets about 150 messages a day. Most are repetitive: "where is my order", "refund not received", "send my invoice". Staff spend most of their time reading, sorting, looking for the order ID and typing near-identical replies. The urgent ones (a swelling power bank, a double charge, a legal threat) are buried among the routine ones.

## What ReplyDesk does

1. Sorts each message into a category and an urgency, so urgent ones are seen first.
2. Pulls out the details (customer name, order ID, product, what they want), and never invents a missing one.
3. Drafts a short reply that follows the store's reply guidelines (`agents/guidelines.md`).
4. Checks the draft against the guidelines and lists any problems.
5. Shows all of this to a human, who approves, edits or rejects. Nothing is sent without a human click.

It also keeps an audit trail of every AI call and measures how often drafts are approved without edits.

## Out of scope

- Sending real emails (approving marks the reply as sent).
- Reading real inboxes (messages arrive through a form, the API, or a CSV import).
- Looking up real order or tracking data. The AI only knows what is in the message.
- Issuing refunds or making any decision. Humans decide; the AI drafts.
- Multiple businesses, multiple languages beyond English and simple Hinglish, chat or phone support.

## Labelling rules

These rules decide the "correct" labels in `eval/emails.csv` and are given to the Sorter agent.

**Category**: label by *the action the customer needs*, not by their mood. An angry message about a late order is `order_status`.

| Category | Use when the customer... |
|---|---|
| `billing` | has a problem with a payment that is not a return: double charge, money deducted with no order, wrong price, coupon, EMI, cashback, invoice, fees. |
| `order_status` | asks about an order not yet fully delivered: where is it, delay, change address, reschedule, cancel before delivery, an item missing from the parcel, "delivered" but not received. |
| `technical` | has a product that doesn't work or needs help using it: defects, setup, compatibility, overheating, safety. |
| `refund` | wants money back for an order: returning a product, refund status, refund for a cancelled or damaged order, return policy questions. |
| `complaint` | mainly reports a bad experience with the store's service (rude or careless courier, ignored emails, long waits, misleading listing, spam) rather than asking for a specific fix to an order. |
| `other` | isn't a support request for an existing order: pre-sale questions about stock or delivery areas, job enquiries, sales pitches, spam, thank-you notes, test messages. |

If a message has two problems, label the one that needs action first (usually the one involving money or safety).

**Urgency**

| Urgency | Use when |
|---|---|
| `high` | safety risk (overheating, swelling, sparks, burning smell); money taken wrongly (double charge, deducted with no order, charged after cancelling); an expensive order lost; legal or chargeback threat; suspected fraud; repeated contact with no answer. |
| `medium` | a real problem with one order: defect, delay, damaged or wrong item, refund pending, missing part. |
| `low` | questions, information requests, feedback, anything with no harm from waiting a day. |

**Details** (`eval/emails.csv` columns starting with `exp_`): only what is written in the subject or body. A name counts only if the customer writes it (for example, a sign-off). An empty cell means the correct answer is `null`. Order IDs look like `PP-123456`.
