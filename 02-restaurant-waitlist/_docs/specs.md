# Configurable Restaurant Waitlist Manager

## 1. Product summary

A configurable, staff-first restaurant waitlist and table-management application for independent table-service venues.

Guests can join a venue's waitlist from a mobile-friendly QR-code or link page. Staff can manage tickets, tables, estimated waits, notifications, seating, cancellations, and no-shows from an authenticated dashboard.

The application is designed for one configurable venue per installation. It is suitable for different cuisines, table layouts, and service styles rather than being hard-coded to a particular restaurant or location.

The application will be developed using a controlled AI-assisted, specification-first workflow. Module 2 ends with a locally running frontend and FastAPI backend, an OpenAPI contract, automated tests, and data persisted in SQLite through SQLAlchemy.

## 2. Problem

Independent restaurants may manage walk-in queues with paper lists, spreadsheets, verbal handovers, or overly complex reservation systems. During busy periods, staff need a reliable way to:

- Capture walk-in parties accurately.
- Give guests a ticket and an estimated wait.
- Let guests wait elsewhere and check their status.
- Match parties to suitable tables.
- Notify guests when a table is ready.
- Handle cancellations, changes, no-shows, and large-party enquiries.
- Keep useful contact and activity information available to authorised staff.

## 3. Product goals

- Provide a fast QR-based guest self-check-in flow.
- Provide an authenticated staff dashboard for queue and table operations.
- Support configurable venue branding, policies, messages, schedules, tables, and waitlist rules.
- Use stable human-readable ticket codes such as `A-001`, `B-002`, and `C-003`.
- Make wait estimates transparent and staff-overridable.
- Preserve guest privacy while allowing staff to contact guests when necessary.
- Maintain a clear audit trail for important status changes and notifications.
- Build the application incrementally: mocked frontend service, OpenAPI contract, FastAPI in-memory backend, then SQLAlchemy with SQLite.
- Keep the backend database-agnostic so PostgreSQL can be used later without rewriting the application flow.

## 4. Non-goals

The following are outside the Module 2 MVP:

- Reservations and booking calendars.
- POS, payment, ordering, kitchen, or loyalty integrations.
- Menu-item management.
- Real SMS, WhatsApp, push, or email delivery to guests.
- Production deployment, containers, CI/CD, and infrastructure automation.
- Observability stacks, operational alerting, and AI incident response.
- Native mobile applications.
- Multiple venues or tenant switching.
- Multi-language content.
- Full holiday and exception-calendar management.
- Automatic no-show background jobs.
- Predictive or AI-generated wait-time forecasting.
- Guest accounts and passwords.
- Password reset, email verification, or enterprise identity management.
- Advanced analytics and revenue reporting.
- Antivirus scanning or cloud object storage for uploaded logos.

The application should still provide extension points for later notification providers, deployment, and operational tooling.

## 5. Users and roles

### Guest

A guest joins the queue through a QR code or public link without creating an account. The guest receives a private status link and can view their own ticket, status, messages, estimated wait, and return-by time. The guest can cancel their active waitlist entry.

### Staff / host

A staff member uses an authenticated dashboard to review and manage active parties, tables, wait estimates, notifications, seating, cancellations, and no-shows. Staff can view guest contact details that are required for operations.

### Admin / manager

An admin or manager can do everything staff can do and can configure the venue, staff access, tables, schedules, waitlist rules, logo, policies, and messages.

## 6. Initial setup and authentication

The first staff account is created through a local setup wizard rather than using a permanently seeded default password.

The setup wizard should:

- Detect that no staff account exists.
- Ask for a manager name, username or email, and password.
- Validate required fields and password strength.
- Create the first admin/manager account with a securely hashed password.
- Require login before accessing the staff dashboard.
- Prevent the setup wizard from being used again after an initial account exists.

Staff authentication should use bearer tokens or an equivalent session mechanism. Staff and admin API endpoints must be protected. Guests do not need accounts; their access is through an opaque status token.

A development-only reset or seeded demo-data command may be provided, but the normal user experience should use the setup wizard.

## 7. Venue configuration

One venue is supported per installation. The venue remains a separate entity in the data model so multiple-venue support can be added later.

The admin can configure:

- Venue display name.
- Contact phone number.
- Staff notification email address.
- Timezone, defaulting to `Australia/Melbourne`.
- Optional logo.
- Optional external menu URL.
- Maximum online party size.
- Default wait estimates by party-size class.
- Waitlist entry mode.
- Grace period in minutes.
- Weekly waitlist schedule.
- Manual queue override: follow schedule, open now, or closed now.
- Guest-facing messages and staff notification templates.

The application does not store or manage menu items. If a menu URL is configured, the public page may provide a link to the restaurant's existing menu.

## 8. Logo upload

The venue can have one optional uploaded logo. The same logo is shown across the staff dashboard, settings preview, guest check-in page, and guest status page.

Rules:

- Accept PNG, JPEG/JPG, and WebP only.
- Maximum file size is 2 MB.
- Reject SVG, GIF, PDF, documents, archives, and other formats in the MVP.
- Validate the actual file content on the backend, not only the filename or browser MIME type.
- Generate a server-side filename.
- Store the local MVP file in a controlled backend uploads directory.
- Replacing a logo removes the previous active logo when possible.
- Removing a logo returns the venue to the neutral default logo.
- The logo must have useful alternative text.

## 9. Tables

An admin can create, edit, activate, deactivate, and remove tables.

Each table has:

- Display name or number.
- Minimum capacity.
- Maximum capacity.
- Active/inactive state.
- Current availability state.
- Optional notes.

The MVP supports table capacities such as 2, 4, and 6. Future versions may support table combinations. A party cannot be seated at a table that is unavailable or whose capacity is insufficient.

## 10. Opening schedule

The venue can configure a weekly waitlist schedule with one or more sessions per day.

Each session includes:

- Day of week.
- Opening time.
- Closing time.

The schedule supports split sessions such as lunch and dinner. The venue timezone is used when determining whether the waitlist is open.

Manual override options:

- Follow schedule.
- Open now.
- Closed now.

When the waitlist is closed:

- New guest submissions are blocked.
- The public page shows a configurable closed message.
- Existing active entries remain visible and manageable to staff.

Holiday calendars and one-off exceptions are future enhancements.

## 11. Waitlist entry modes

The venue can choose one of two modes:

### Automatic mode

This is the default. A valid QR submission immediately becomes `waiting`. Staff can review, edit, or cancel it later.

### Staff-review mode

A valid QR submission initially becomes `pending`. Staff must approve it before it becomes `waiting`.

Staff-review mode is useful for large queues, closing periods, duplicate submissions, or venues that want to verify special seating requests.

The mode is configurable by an admin and should not change existing entries retroactively.

## 12. Guest QR check-in flow

1. Guest scans the venue QR code or opens the public waitlist link.
2. The page displays the venue logo, venue name, opening status, and join message.
3. Guest enters:
   - Lead guest or party name.
   - Party size.
   - Mobile number.
   - Optional seating or accessibility note.
4. The guest reads the waitlist policy.
5. The guest must check an acknowledgement checkbox.
6. The backend validates the request.
7. If accepted, the system creates a ticket or large-party enquiry.
8. The guest receives a confirmation page with the ticket code or enquiry reference.
9. The page provides a private status link using an opaque access token.

The form must not collect unnecessary information such as address, date of birth, or marketing preferences.

## 13. Party-size limits and large-party enquiries

The admin configures the maximum party size that can join the normal online waitlist. The default is 12.

The form must reject:

- Zero or negative party sizes.
- Non-integer values.
- Empty or excessively long names.
- Invalid mobile numbers.

For a party size above the configured maximum:

- Do not create a normal waitlist ticket.
- Create a large-party enquiry with a unique enquiry reference.
- Store the guest's name, mobile number, requested party size, note, and submission time.
- Show the guest a message explaining that the enquiry is not a confirmed booking or waitlist position.
- Create a staff notification event addressed to the configured staff email.
- Use a mock or console notification provider locally; real email delivery is optional and configuration-dependent.

The large-party customer messages must clearly explain that staff will contact them to discuss options.

## 14. Ticket numbering

Normal waitlist tickets use a party-size class and one daily sequence number.

Default classes:

- `A`: 1–2 guests.
- `B`: 3–4 guests.
- `C`: 5–6 guests.
- `D`: 7–12 guests.

The numeric sequence is shared across all classes and scoped to the venue's local service date.

Example:

```text
A-001
C-002
B-003
```

Rules:

- The sequence resets on the next local service date.
- Cancelled and no-show tickets are not reused.
- The server assigns the number transactionally.
- Concurrent submissions must not receive the same number.
- The internal database identifier is separate from the ticket code.
- The ticket code remains stable if staff later edit party size.
- The original class is retained for the customer-facing ticket.
- The dashboard can show the current seating class separately after a party-size change.

## 15. Review flags

The application should not alter a guest's ticket code when staff change details. Instead, it displays an explicit review flag.

A ticket may be marked `review_required` for reasons such as:

- Party size changed.
- Current size no longer matches the original class.
- Seating or accessibility note requires attention.
- Staff explicitly requested review.
- Other operational exception.

The staff dashboard should show a visible `Review required` badge, the reason, and a filter for tickets requiring review. The badge must not rely on colour or a symbol alone.

## 16. Wait estimates

Wait estimates are suggestions, not promises.

The admin can configure default estimates by party-size class, for example:

- A: 15 minutes.
- B: 25 minutes.
- C: 40 minutes.
- D: 55 minutes.

The system may produce a basic suggested estimate using configured class defaults and active queue information. Staff can override the suggestion before approving or notifying a guest.

The guest sees the staff-approved estimate or range. The UI must label it as an `Estimated wait`.

The system must not claim to predict seating time accurately or use AI forecasting in the MVP.

## 17. Queue ordering and seating

The application must not promise strict public first-in-first-out seating.

The staff dashboard should organise active entries by:

1. Status.
2. Seating compatibility and available tables.
3. Party-size class or current seating class.
4. Arrival time within comparable groups.

The dashboard should make like-for-like ordering clear. A two-person party may be seated before a six-person party if an appropriate table is available.

Staff retain final discretion. If staff seat a later compatible party ahead of an earlier one, the system should support an optional seating-override reason such as `table compatibility`.

A party can be seated only when staff select an available compatible table. Seating marks the party as `seated` and the table as occupied.

## 18. Status model

Normal waitlist statuses:

```text
pending
waiting
notified
seated
completed
cancelled
no_show
```

Recommended transitions:

```text
pending   -> waiting
pending   -> cancelled
waiting   -> notified
waiting   -> cancelled
notified  -> seated
notified  -> cancelled
notified  -> no_show
seated    -> completed
```

Staff may return an accidentally notified entry from `notified` to `waiting` through a controlled correction action.

Cancelled and no-show entries leave the active queue but remain available in history.

## 19. Guest cancellation

A guest can cancel an active entry from the private status page.

The cancellation flow:

- Shows the ticket code and party details.
- Requires confirmation.
- Changes the entry to `cancelled`.
- Records the cancellation time and actor as guest.
- Removes the entry from active queue views.
- Shows the configured cancellation message.

The ticket code is not reused.

## 20. Grace period and overdue notifications

The admin configures a grace period, defaulting to 10 minutes.

When staff notify a party:

- Record the notification time.
- Calculate and record `return_by_at`.
- Render the configured table-ready message.
- Display the notification on the guest status page.

If the return-by time has passed:

- Show a text label such as `Needs attention`.
- Use an amber or red visual cue in addition to text.
- Display the notification time and return-by time.
- Prioritise the entry in a staff attention filter.
- Allow staff to contact the guest, extend the grace period, mark seated, or mark no-show.

The system does not automatically mark a no-show in the MVP.

## 21. Configurable messages

The admin can configure separate messages for:

- Join message.
- Policy acknowledgement text.
- Confirmation message.
- Table-ready message.
- Cancellation message.
- No-show message.
- Closed waitlist message.
- Large-party enquiry message.
- Large-party enquiry confirmation.
- Staff large-party email subject and body.

Messages support a safe allowlist of variables:

```text
{restaurant_name}
{guest_name}
{ticket_code}
{party_size}
{estimated_wait_minutes}
{grace_period_minutes}
{return_by_time}
{enquiry_reference}
{submitted_at}
```

Do not allow arbitrary code or unsafe HTML in message templates.

The application should store a policy version and the relevant message snapshot when a guest acknowledges the policy or staff notify a party. Editing venue settings must not rewrite historical records.

## 22. Notification framework

The application should use a provider abstraction so delivery mechanisms can be added later without changing waitlist logic.

Suggested providers:

```text
ConsoleNotificationProvider
MockNotificationProvider
EmailNotificationProvider
SmsNotificationProvider
WebhookNotificationProvider
```

Module 2 should implement:

- In-app guest status updates.
- Staff dashboard notification events.
- Console or mock delivery for local development.
- A provider interface and notification records.

Real SMS, WhatsApp, email, or push delivery is not required for the default local setup. The large-party staff alert should be represented through the same mock or console provider unless SMTP is explicitly configured.

Each notification record should store:

- Recipient type.
- Channel.
- Template type.
- Rendered message.
- Delivery status: queued, sent, or failed.
- Provider message identifier when available.
- Error message when delivery fails.
- Created and sent timestamps.

## 23. Privacy and staff contact data

The application stores the minimum data required to operate the waitlist:

- Guest or party name.
- Mobile number.
- Party size.
- Optional seating/accessibility note.
- Queue status and timestamps.
- Policy acknowledgement.
- Notification and cancellation history.

Staff can view contact details in the authenticated dashboard and use a click-to-call link where supported.

The public guest page must not expose:

- Other guests or queue entries.
- Public queue lists containing names.
- Internal notes.
- Staff-only review reasons.
- Notification provider errors.
- Policy audit metadata.

Guest access uses an opaque, unguessable status token. Ticket codes alone must not grant access to private details.

Automated data-retention rules are out of scope, but staff can filter historical entries by service date. A future version should add retention and deletion policies.

## 24. Accessibility and responsive design

The public QR flow is mobile-first. The staff dashboard works on desktop and tablet screens.

Requirements:

- Visible labels for every form field.
- Keyboard-accessible controls.
- Logical focus order and visible focus states.
- Clear text errors associated with the relevant field.
- Errors must not be communicated by colour alone.
- Adequate touch targets.
- Accessible alternative text for the venue logo.
- Responsive layout for narrow screens.
- Status badges include text as well as colour and icons.
- Custom messages remain readable and do not require horizontal scrolling.

## 25. Data entities

The initial data model should include entities similar to:

### Venue

Name, contact details, staff notification email, timezone, logo path, menu URL, maximum party size, entry mode, grace period, schedule mode, and manual open/close override.

### VenueMessageSettings

Message templates, template version, updated timestamp, and policy version.

### StaffUser

Name, username or email, password hash, role, active state, and timestamps.

### Table

Name, capacity, active state, availability state, and notes.

### WaitlistEntry

Internal ID, service date, daily ticket number, original party class, current party size, guest name, phone number, notes, status, estimated wait, review flag, access token, timestamps, policy snapshot, and notification information.

### LargePartyEnquiry

Reference, guest name, phone number, requested party size, notes, status, contact timestamps, and notification status.

### Notification

Recipient type, channel, template, rendered message, delivery status, provider identifier, errors, and timestamps.

### StatusEvent / ActivityLog

Entry identifier, previous status, new status, actor type, actor identifier where applicable, reason, and timestamp.

## 26. API and architecture expectations

The frontend must centralise all backend calls in one service layer. The mocked service must implement the same conceptual interface as the eventual backend client.

The repository should contain:

```text
frontend/
backend/
openapi.yaml
_docs/plan.md
tests/
AGENTS.md
docs/ai-usage-report.md
```

Development stages:

1. Build an interactive frontend using a mocked service layer.
2. Derive `openapi.yaml` from the frontend service interface.
3. Implement FastAPI endpoints against the OpenAPI contract using an in-memory store.
4. Connect the frontend to FastAPI and verify the end-to-end flows.
5. Replace the in-memory store with SQLAlchemy and SQLite.
6. Preserve the service and API contracts while changing persistence.

The backend should separate routers, schemas, application services, repositories, authentication, notification providers, and persistence models sufficiently to support later changes.

## 27. Testing expectations

Tests must cover behavior in the product specification and API contract.

Important cases include:

- Initial setup wizard creates the first admin account.
- Setup cannot be repeated after an account exists.
- Staff login succeeds with valid credentials and fails safely with invalid credentials.
- Protected endpoints reject unauthenticated requests.
- Guests can submit valid QR entries.
- Policy acknowledgement is required.
- Closed waitlists reject new entries with the configured message.
- Automatic mode creates `waiting` entries.
- Staff-review mode creates `pending` entries.
- Invalid party sizes and phone numbers are rejected.
- A party above the maximum creates a large-party enquiry rather than a ticket.
- Large-party staff notification is created.
- Daily ticket numbers are shared across classes and are not reused.
- Concurrent ticket creation does not create duplicate numbers.
- Party-size edits preserve ticket codes and create review flags.
- Queue ordering groups compatible party sizes and respects arrival order within groups.
- Staff cannot seat a party at an unsuitable or occupied table.
- Notifications record rendered messages and return-by times.
- Overdue notified entries show a needs-attention state.
- Guests can cancel their own active entry but cannot access another entry.
- Logo upload validates type, actual content, and size.
- SQLite persistence survives backend restart.
- Public responses do not expose staff-only or other-guest data.

## 28. Future enhancements

Potential follow-up work includes:

- Real SMS, email, WhatsApp, and push integrations.
- Automatic no-show timers and scheduled background tasks.
- Table combinations and floor-plan views.
- Reservations and bookings.
- Multi-venue management.
- Settings import/export.
- Holiday and special-hours calendars.
- Data retention and deletion tools.
- Guest language preferences.
- Analytics on wait times, walkaways, table turnover, and no-shows.
- POS and reservation-platform integrations.
- S3 or equivalent object storage for logos.
- Production deployment, Docker, PostgreSQL, CI/CD, and observability.
