# CLAUDE.md

This file gives Claude Code (and any other agent working in this repo) the
concept and scope of the project. Read it before making design decisions —
it defines what the bot is supposed to do, and just as importantly, what it
is *not* supposed to do.

## What this is

A Telegram bot that auto-replies to a business account's personal messages
based on trigger rules configured by the account owner.

It is **not** a standalone bot. It only works through
[Telegram Business](https://core.telegram.org/bots/business): the account
owner connects it as their business chatbot (Settings → Telegram Business →
Chatbots → enter the bot's username). Once connected, Telegram forwards the
owner's incoming personal messages to the bot as `business_message` updates
(via `business_connection_id`), and the bot can reply on the owner's behalf.
A bot that is merely added to a group/channel, without an active business
connection, has nothing to do.

There is exactly one bot deployment. Every Telegram user who connects it via
Telegram Business becomes an independent owner with their own set of rules;
the bot is multi-tenant by `business_connection_id` / owner's Telegram user
id, not by bot instance.

## Core flow

### Onboarding (one step from the user's point of view)

1. User sends `/start` to the bot in their private chat with it.
2. Bot checks whether it has an active business connection for this
   Telegram user (i.e. it has received a `business_connection` update with
   `is_enabled=true` for them).
3. If not connected yet: bot explains how to connect it (Settings →
   Telegram Business → Chatbots → enter the bot's username) and stops there.
   The bot must keep listening for `business_connection` updates so it can
   detect the connection once the user completes it on their side.
4. Once connected: bot shows the main menu.

There is no further setup step. Connecting the business account *is* the
onboarding.

### Main menu

Two options only:

- **Add rule**
- **My rules** (list of existing rules)

### Adding a rule (wizard)

Order matters — matching options are configured first, then triggers, then
the reply:

1. **Matching options.** Before any trigger text is entered, the user picks
   how triggers for this rule should be matched:
   - Case sensitivity: exact case vs. case-insensitive.
   - Word boundaries: trigger must match a whole word vs. trigger may occur
     as a substring inside other words.
2. **Triggers.** The user enters the trigger word(s)/phrase(s) for the rule.
   A single rule accepts multiple triggers at once (e.g. entered one per
   line, or comma-separated — exact input UX is an implementation detail).
   The rule fires if **any** of its triggers matches the incoming message
   (OR semantics within a rule).
3. **Reply text.** What the bot sends back when the rule matches.
4. **Chat scope.** Which of the owner's business chats the rule applies to:
   - **All chats** — matches a message from anyone writing to the business
     account, or
   - **A specific contact** — matches only messages from one chosen Telegram
     user. The user is picked via Telegram's native contact-picker button
     (`request_users`), not typed in — the bot only ever compares by the
     resulting numeric Telegram user id, never by name/username (those may
     change or be absent).

Once all four are provided, the rule is saved and becomes active
immediately.

### Overlap prevention

Two active rules must never be able to match the same incoming message —
this is enforced at creation/edit time, not at message-matching time. When
a rule is created or edited, its trigger set is checked against every other
*active* rule owned by the same user that could apply to the same chat
(under the matching options in effect for each rule); if an overlap is
found, the bot rejects the input and asks the user to adjust it. Two rules'
chat scopes are only compared against each other when deciding whether they
*could* both apply to the same message: "all chats" can collide with
anything, and two "specific contact" rules only collide when they name the
same contact. There is no runtime priority/ordering system for resolving
overlapping matches — overlaps are simply not allowed to exist. The exact
trigger overlap-detection algorithm (e.g. how substring-mode triggers are
compared against whole-word-mode triggers from another rule) is an
implementation detail to work out during development, but the product
behavior — reject at input time — is fixed.

### Rule list / editing

"My rules" lists **all** of the user's rules, active and inactive alike
(each shown with its status), since disabled rules must stay reachable to be
re-enabled. Only active rules take part in matching and in the overlap
check. Selecting one opens an edit
view where the user can:

- Edit the matching options, triggers, reply text, and/or chat scope
  (subject to the same overlap check as creation).
- Toggle the rule active/inactive without deleting it. Inactive rules are
  excluded from matching and from overlap checks, but stay in the list so
  they can be re-enabled later. Re-enabling runs the same overlap check as
  creation (other rules may have taken over its triggers while it was off);
  if it now conflicts, re-enabling is refused until the conflict is
  resolved.

### Scope boundary

This is the entire feature set. Deliberately **out of scope** unless the
user asks for it later: rule priorities/ordering, scheduling or expiry,
analytics/usage dashboards, targeting anything other than a single specific
contact or all chats (e.g. groups of contacts, exclusion lists), multi-
language bot UI, deleting rules (disable covers that need), anything about
groups/channels. Do not add any of this speculatively.

## Data model (conceptual)

Not a schema — just the entities and how they relate, for orientation:

- **Owner** — a connected Telegram Business account: Telegram user id,
  `business_connection_id`, connection enabled/disabled state.
- **Rule** — belongs to an Owner: matching options (case sensitivity, word
  boundary), reply text, active/inactive flag, chat scope (nothing = all
  chats, or a specific contact's Telegram user id).
- **Trigger** — belongs to a Rule: the literal trigger text. A Rule has one
  or more Triggers.

### Custom (Premium) emoji

Trigger text and reply text are stored as HTML, not plain text, specifically
so custom emoji survive. Telegram represents a custom emoji as a
`custom_emoji` message entity over a plain fallback glyph — the raw
`.text`/`.caption` never contains the emoji's identity, only the entity does.
Whenever text is captured from the owner (entering triggers/reply, editing
either), it's converted via aiogram's `html_decoration.unparse(text,
entities)` into HTML, turning each custom emoji into
`<tg-emoji emoji-id="...">fallback</tg-emoji>` (and incidentally preserving
any other formatting the owner typed, e.g. bold/italic — accepted as a side
effect, not a feature to build on). This is also why matching an incoming
business message runs against that same HTML rendering of it, not its raw
text: two different custom emoji can share a fallback glyph, and comparing
by the tag's `emoji-id` is what makes trigger matching "by the actual
emoji" rather than by its visual look-alike. Since the bot's default
`parse_mode` is HTML, stored reply text sends back correctly as-is; anywhere
a trigger/reply preview must NOT be interpreted as HTML (inline button
labels, native alert popups), strip it with `text_format.strip_html_preview`
first.

## Tech stack

- Python 3.11
- [aiogram](https://docs.aiogram.dev/) 3.x — needs Business API support
  (`business_connection`, `business_message` and related updates), so keep
  aiogram reasonably current.
- SQLAlchemy 2.0 (async) as the ORM, Alembic for migrations.
- SQLite for local development, PostgreSQL for production — same models,
  swapped via `DATABASE_URL`.
- Docker / Docker Compose for running the bot alongside Postgres.
- Package/environment management via [uv](https://docs.astral.sh/uv/).

## Repository layout

```
src/telegram_message_trigger/
  config.py          Settings (env-driven), see .env.example
  main.py             Bot/Dispatcher bootstrap, entry point
  db/
    base.py           Declarative base
    session.py        Async engine/session factory
  handlers/           aiogram routers (message/menu handlers)
  keyboards/          Inline/reply keyboard builders
  states/             aiogram FSM state groups (rule-creation wizard, etc.)
  services/           Business logic (matching, overlap checks, etc.)
  middlewares/        aiogram middlewares
alembic/              DB migrations
tests/
```

## Conventions

- Code, comments, docs, and commit messages: **English**.
- Bot-facing UI text (messages, button labels): **Russian** — this is a
  product decision, not a limitation; do not add i18n scaffolding for it.
- Business logic (matching, overlap detection, rule state transitions)
  belongs in `services/`, not inline in handlers — handlers should stay
  thin (parse input, call a service, render a keyboard/message).
