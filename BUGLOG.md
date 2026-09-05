# Build Log — what broke, and how I got out of it

## [Phase 2] ngrok requires authtoken — ERR_NGROK_4018
- What broke: `ngrok http 8000` rejected with "This ngrok session is not authenticated"
- Root cause: ngrok removed anonymous tunnel access; free account + authtoken now mandatory
- Fix (deferred to Phase 7): sign up at ngrok.com, run `ngrok config add-authtoken <token>` once
- Decision: deferred live webhook verification to end of build, since the rest of the
  pipeline (diagnosis → decision → execution) doesn't depend on it and runs off seeded data

## [Phase 7 / Part 1] Razorpay webhook signature verification — TypeError on secret
- What broke: `razorpay.Utility.verify_webhook_signature(...)` threw
  `TypeError: missing 1 required positional argument: 'secret'`
- Root cause: called `Utility.verify_webhook_signature` as if it were a static
  method. It's actually an instance method accessed via a Client object
  (`client.utility.verify_webhook_signature(...)`), not `razorpay.Utility`
  directly. Calling it unbound meant Python silently passed the payload
  string in as `self`, shifting every argument over by one.
- Fix: instantiate `razorpay.Client(auth=(KEY_ID, KEY_SECRET))` first, then
  call `client.utility.verify_webhook_signature(payload, signature, secret)`
- Time lost: ~20 min

## [Phase 7 / Part 1] Webhook crash on empty `notes` field
- What broke: `AttributeError: 'list' object has no attribute 'get'` on
  `payment_entity.get("notes", {}).get("name", ...)`
- Root cause: Razorpay returns `notes` as an empty list `[]` (not `{}`) when
  no notes were attached to the payment, since `notes` is technically a
  free-form key-value store that defaults to an empty array server-side.
  `.get()` on a list doesn't exist, so it crashed instead of falling back.
- Fix: explicitly check `isinstance(notes, dict)` before calling `.get()`,
  default to `{}` otherwise
- Time lost: ~10-15 min

## [Phase 7 / Part 1] Razorpay webhook — three chained bugs before it worked
- What broke: Variable name collision: reused `event` as both the webhook's event-name
  string (`data.get("event")`) and the newly created `RevenueEvent` model
  instance, so `process_event_immediately()` sometimes received the string
  instead of the model. 
- Fix: Fixed by renaming to `webhook_event_name` and
  `revenue_event` respectively so there's no ambiguity.
- Time lost: ~25 min

## Injected overdue invoices never escalated
- What broke: Inject Live Event created an `overdue_invoice` RevenueEvent with
  no linked Invoice record. Diagnosis reads `days_overdue` from
  `revenue_event.invoice.due_date` — with no invoice, it silently defaulted
  to 0 days, so every injected invoice was classified `recently_overdue`
  regardless of amount, and never reached the `severely_overdue` root cause
  that has an `escalate_human` rule attached.
- Fix: Inject Live Event now creates a real Invoice (backdated 45 days) and
  links it to the RevenueEvent before running the pipeline.
- Time lost: ~15 min
