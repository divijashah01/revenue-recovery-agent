# Build Log — what broke, and how I got out of it

## [Phase 2] ngrok requires authtoken — ERR_NGROK_4018
- What broke: `ngrok http 8000` rejected with "This ngrok session is not authenticated"
- Root cause: ngrok removed anonymous tunnel access; free account + authtoken now mandatory
- Fix (deferred to Phase 7): sign up at ngrok.com, run `ngrok config add-authtoken <token>` once
- Decision: deferred live webhook verification to end of build, since the rest of the
  pipeline (diagnosis → decision → execution) doesn't depend on it and runs off seeded data