Build a React + TypeScript frontend prototype for a configurable restaurant waitlist manager.

This is Step 2 of a full-stack course project. The product specification has already been completed. Do not repeat the planning process.

# Non-negotiable decisions

Use these decisions without asking clarification questions:

- Use React + TypeScript.
- Build the frontend only.
- Use a local in-memory mock service.
- Do not use Supabase, Firebase, a hosted database, or any external backend service.
- Do not create a FastAPI, Node, or other backend.
- The backend will be implemented separately later with FastAPI.
- Do not create SQLite, SQLAlchemy, migrations, or database schemas.
- Do not create `openapi.yaml` yet.
- Do not implement real authentication.
- Create only a mocked staff login interaction with a clearly defined service method.
- Do not implement real email, SMS, WhatsApp, push notifications, or webhooks.
- Record notification actions as mocked in-app events.
- Do not implement real file upload or file storage.
- Use a neutral default logo placeholder.
- Do not implement reservations or bookings.
- Do not implement POS, payments, ordering, loyalty, or menu-item management.
- Do not implement multiple venues or tenant switching.
- Do not add AI functionality to the product.
- This is an AI-assisted project, not necessarily an AI-powered product.
- Do not add features that are not listed in this prompt.
- If a detail is not specified, choose the smallest local mock implementation that keeps the frontend interactive.
- Do not pause to ask for approval; implement the stated decisions.

# Most important architectural rule

The frontend must communicate with a backend-shaped service interface, even though the backend does not exist yet.

Create a clear service boundary:

- `src/services/waitlistService.ts`
  - Shared TypeScript domain types.
  - Request and response types.
  - A `WaitlistService` interface.

- `src/services/mockWaitlistService.ts`
  - An implementation of `WaitlistService`.
  - Seeded in-memory data.
  - Simulated asynchronous operations.
  - All mock business logic.
  - No direct use of fetch, axios, Supabase, Firebase, or a database.

- `src/services/index.ts`
  - Exports the active mock service instance.

Every operation that could eventually require a backend must go through this service:

- Login.
- Venue retrieval and updates.
- Waitlist retrieval and creation.
- Guest status retrieval.
- Guest cancellation.
- Staff approval and cancellation.
- Guest notification.
- Seating.
- No-show and completion actions.
- Table retrieval.
- Large-party enquiries.
- Notification event creation.

React components and route pages must not:

- Call `fetch`.
- Call `axios`.
- Call Supabase or Firebase.
- Read or write a database.
- Store application state in localStorage.
- Import mock data directly.
- Generate ticket numbers themselves.
- Apply business rules that belong in the service.

The mock service owns:

- Seeded data.
- Validation.
- Ticket generation.
- Status changes.
- Party-size classification.
- Table compatibility.
- Notification events.
- Simulated delays.

The service method names and request/response types must be explicit and serializable because a separate agent will later use them to create `openapi.yaml` and a FastAPI backend.

# Application purpose

The application helps an independent table-service restaurant manage walk-in guests.

Guests can:

- Join a waitlist through a mobile-friendly QR-code or link page.
- Receive a ticket such as `A-001`, `B-002`, or `C-003`.
- See their estimated wait and status.
- View a table-ready message.
- Cancel their own active waitlist entry.

Staff can:

- View active waitlist entries.
- Review party sizes and seating notes.
- Notify guests.
- Assign a compatible table.
- Mark guests seated, completed, cancelled, or no-show.
- See overdue notified tickets that need attention.

The application supports one configurable demo venue.

# Routes and screens

Implement these screens and routes.

## 1. Staff login: `/login`

Create a mocked staff login screen.

Requirements:

- Include a username/email field.
- Include a password field.
- Any non-empty demo credentials may succeed.
- Use the service-layer `login` method.
- After successful login, navigate to `/staff`.
- Make it clear in the UI that authentication is mocked for this frontend prototype.
- Show validation errors for empty fields.
- Do not implement real authentication or password storage.

## 2. Staff dashboard: `/staff`

Create the main staff dashboard.

Show:

- Venue name.
- Default logo placeholder.
- Current waitlist state.
- Current service date.
- Summary cards:
  - Active waiting.
  - Pending review.
  - Notified.
  - Needs attention.
- Filters for:
  - Status.
  - Party-size class.
  - Review-required entries.
  - Needs-attention entries.
- Waitlist entries containing:
  - Ticket code.
  - Guest name.
  - Party size.
  - Original party class.
  - Current seating class.
  - Arrival time.
  - Estimated wait.
  - Status.
  - Review-required badge where applicable.
  - Overdue/needs-attention badge where applicable.
- Clear empty states.
- Loading states.
- Error states.

Staff actions:

- Approve a pending entry.
- Cancel an entry.
- Notify a guest.
- Seat a guest.
- Mark a notified guest as no-show.
- Complete a seated party.
- Optionally return an accidentally notified guest to waiting.
- Add an optional seating override reason when seating a later compatible party.

Use confirmation dialogs for destructive actions.

Do not show guest phone numbers in the main list. Provide a staff-only details panel or drawer where contact information may be viewed.

## 3. Staff tables: `/staff/tables`

Show the venue table inventory.

Each table should display:

- Table name or number.
- Capacity.
- Available or occupied state.
- Occupying ticket when occupied.

When seating a guest:

- Show only compatible available tables.
- Do not allow seating at an occupied table.
- Do not allow seating at a table with insufficient capacity.
- Mark the selected table occupied after seating.
- Mark the table available after the party is completed.

Do not implement floor plans or table combinations.

## 4. Staff settings: `/staff/settings`

Create a basic venue settings screen.

Show editable fields for:

- Venue name.
- Contact phone.
- Staff notification email.
- Menu URL.
- Maximum online party size, default 12.
- Grace period, default 10 minutes.
- Entry mode:
  - Automatic.
  - Staff review.
- Waitlist open/closed state.
- Default wait estimates for party classes A, B, C, and D.

Show:

- Neutral logo placeholder.
- Logo preview area.
- Text explaining that real logo upload is deferred to the backend phase.
- Editable message fields:
  - Join message.
  - Policy acknowledgement message.
  - Confirmation message.
  - Table-ready message.
  - Cancellation message.
  - Closed waitlist message.
  - Large-party message.
  - Large-party confirmation message.

Include a preview of the guest-facing messages.

Use the service layer for saving settings.

Do not implement real binary file uploads or file storage.

## 5. Public guest join page: `/join`

Create a mobile-first public guest join page.

Show:

- Venue logo placeholder.
- Venue name.
- Open or closed state.
- Configured join message.
- Current maximum online party size.
- Guest or party name field.
- Party size field.
- Mobile number field.
- Optional seating/accessibility note field.
- Configured waitlist policy.
- Required policy acknowledgement checkbox.
- Join waitlist button.

Form rules:

- The policy checkbox is unchecked by default.
- The form cannot submit without acknowledgement.
- Name is required.
- Party size is required and must be a positive integer.
- Mobile number is required and must have basic valid formatting.
- Optional notes may be left blank.
- Show clear text validation errors beside the relevant fields.
- Do not communicate errors through colour alone.
- Use the mock service for submission.

If the waitlist is closed:

- Block new submissions.
- Show the configured closed message.
- Keep the form unavailable or clearly disabled.

## 6. Public guest status page: `/status/:accessToken`

Create a public status page for one guest entry.

Use the opaque mock access token from the service layer.

Show only the entry associated with that token:

- Venue logo placeholder.
- Venue name.
- Ticket code.
- Guest name.
- Party size.
- Current status.
- Estimated wait.
- Relevant configured message.
- Notification time if notified.
- Return-by time if notified.
- Cancellation action while cancellation is allowed.

If notified:

- Show a prominent table-ready state.
- Show the ticket code.
- Show the return-by time.
- Show the configured table-ready message.

If the return-by time has passed:

- Show `Needs attention` or `Return time passed` as visible text.
- Use an additional amber/red visual cue.
- Do not rely on colour alone.

Cancellation:

- Require confirmation.
- Change the entry to cancelled through the mock service.
- Show the configured cancellation message.
- Do not show other guests.
- Do not show the guest’s phone number.
- Do not show internal notes or review reasons.

## 7. Large-party enquiry state

If the submitted party size exceeds the configured maximum:

- Do not create a normal waitlist ticket.
- Do not assign a queue position.
- Create a mocked large-party enquiry through the service layer.
- Generate an enquiry reference.
- Show a clear customer message.
- Explain that this is not a confirmed booking or waitlist position.
- Explain that staff will contact the guest to discuss options.
- Create a mocked staff notification event.
- Provide a clear next step for the guest.

Example message:

`For parties larger than 12, please contact the restaurant so we can discuss seating options. Your request has not been added to the waitlist.`

Example confirmation:

`Thanks. We have sent your large-party request to the restaurant. A staff member will contact you to discuss available options. This request is not a confirmed booking or waitlist ticket.`

# Core domain types

Create explicit TypeScript types for at least:

- `Venue`
- `VenueMessageSettings`
- `StaffSession`
- `Table`
- `WaitlistEntry`
- `LargePartyEnquiry`
- `Notification`
- `ActivityEvent`
- `PartySizeClass`
- `WaitlistStatus`
- `EntryMode`
- `WaitlistFilters`
- `CreateGuestEntryRequest`
- `CreateGuestEntryResult`
- `GuestStatus`
- `SeatEntryRequest`
- `UpdateVenueRequest`
- `NotificationResult`
- `LoginRequest`

Use these waitlist statuses:

- `pending`
- `waiting`
- `notified`
- `seated`
- `completed`
- `cancelled`
- `no_show`

Use these party-size classes:

- A: 1–2 guests.
- B: 3–4 guests.
- C: 5–6 guests.
- D: 7–12 guests.

# Ticket rules

Seed realistic ticket codes such as:

- `A-001`
- `B-002`
- `C-003`
- `B-004`

Use one shared daily sequence across all classes.

The mock service must assign ticket numbers, not React components.

Rules:

- The numeric sequence is shared across all party classes.
- The sequence resets by mock service date.
- Cancelled and no-show tickets are not reused.
- Ticket codes remain stable after party-size edits.
- If current party size differs from the original class:
  - Preserve the original ticket.
  - Show the current seating class separately.
  - Set `reviewRequired` to true.
  - Show a `Review required` badge.
  - Show an explanation.

# Queue and seating behavior

Organise staff entries by:

1. Status.
2. Table compatibility.
3. Party-size class or current seating class.
4. Arrival time within comparable groups.

Do not claim that seating is strict FIFO.

A later compatible party may be seated before an earlier incompatible party.

Allow staff to select a suitable available table.

Do not allow:

- Seating at an occupied table.
- Seating at a table with insufficient capacity.
- Seating a cancelled or no-show entry.

When a party is seated:

- Change status to `seated`.
- Mark the table occupied.
- Display the assigned table.

When a seated party is completed:

- Change status to `completed`.
- Mark the table available.

# Wait estimates

Use simple mocked estimates, not predictive intelligence.

Seed default estimates:

- A: 15 minutes.
- B: 25 minutes.
- C: 40 minutes.
- D: 55 minutes.

Requirements:

- Display `Estimated wait`.
- Allow staff to override the estimate through the dashboard.
- Show the approved estimate on the guest status page.
- Do not promise a guaranteed seating time.
- Do not add AI-based wait prediction.

# Notifications

Use a mocked notification provider.

When staff click `Notify`:

- Change the entry to `notified`.
- Record a notification timestamp.
- Calculate a return-by time using the configured grace period.
- Render the configured table-ready message.
- Store a mock notification/activity event.
- Make the guest status page show the notified state.

Do not send real messages.

Represent notification events with fields such as:

- Recipient type.
- Channel.
- Template type.
- Rendered message.
- Delivery status.
- Created timestamp.
- Sent timestamp.
- Optional error message.

The mock provider may mark events as `sent`.

When the return-by time has passed:

- Show `Needs attention` as text.
- Use an additional amber/red visual cue.
- Show the notification time.
- Show the return-by time.
- Allow staff to:
  - Mark seated.
  - Mark no-show.
  - Cancel.
  - Extend the return-by time if supported by the mock service.

# Guest cancellation

Guests can cancel their own active entry from the private status page.

Requirements:

- Show a confirmation dialog.
- Call the mock service using the access token.
- Change status to `cancelled`.
- Remove the entry from active staff queue views.
- Show the configured cancellation message.
- Keep the ticket code reserved.
- Do not reuse the ticket code.

# Mock service methods

Implement a service interface with methods similar to:

```ts
login(input: LoginRequest): Promise<StaffSession>;

getVenue(): Promise<Venue>;
updateVenue(input: UpdateVenueRequest): Promise<Venue>;

getDashboard(serviceDate?: string): Promise<DashboardData>;
listWaitlistEntries(
  filters?: WaitlistFilters
): Promise<WaitlistEntry[]>;

createGuestEntry(
  input: CreateGuestEntryRequest
): Promise<CreateGuestEntryResult>;

getGuestEntry(
  accessToken: string
): Promise<GuestStatus>;

cancelGuestEntry(
  accessToken: string
): Promise<WaitlistEntry>;

approveEntry(
  entryId: string
): Promise<WaitlistEntry>;

cancelEntry(
  entryId: string
): Promise<WaitlistEntry>;

notifyEntry(
  entryId: string
): Promise<NotificationResult>;

seatEntry(
  entryId: string,
  input: SeatEntryRequest
): Promise<WaitlistEntry>;

markNoShow(
  entryId: string
): Promise<WaitlistEntry>;

completeEntry(
  entryId: string
): Promise<WaitlistEntry>;

listTables(): Promise<Table[]>;

createLargePartyEnquiry(
  input: LargePartyEnquiryRequest
): Promise<LargePartyEnquiry>;
```

You may add small methods if needed, but do not expand the feature scope.

Use simulated asynchronous delays so loading states and service errors can be tested.

# Seed data

Seed one neutral venue called `Demo Restaurant`.

Seed:

- Venue settings.
- Default message templates.
- Tables with capacities 2, 4, and 6.
- Several active waitlist entries.
- At least one pending entry.
- At least one waiting entry.
- At least one notified entry.
- At least one entry requiring review.
- At least one overdue notified entry.
- At least one occupied table.
- At least one available compatible table.
- At least one mock notification event.

Use fictional guest data only.

# Design direction

Create a polished but restrained restaurant operations interface.

Staff experience:

- Desktop/tablet-oriented dashboard.
- Clear operational hierarchy.
- Compact but readable queue table/cards.
- Prominent action controls.
- Useful filters.
- Clear table availability.
- Strong visual treatment for `Needs attention` and `Review required`.

Guest experience:

- Mobile-first layout.
- Short form.
- Large readable ticket code.
- Clear estimated wait and status.
- Simple cancellation action.
- No unnecessary content.

Accessibility:

- Visible labels for every form field.
- Keyboard-accessible controls.
- Logical focus order.
- Visible focus states.
- Clear text errors associated with the relevant field.
- Errors must not be communicated by colour alone.
- Adequate touch targets.
- Alternative text for the logo placeholder.
- Status badges must include text, not only colour or icons.
- Responsive layout for narrow phone screens.

Avoid:

- Unnecessary animations.
- Charts.
- Marketing pages.
- Reservation calendars.
- POS screens.
- Ordering flows.
- Menu management.
- Loyalty features.
- Multi-venue features.
- AI features.
- Complex floor plans.
- Real integrations.

# Tests

Add a focused frontend test suite covering:

- Valid guest submission.
- Required policy acknowledgement.
- Required name validation.
- Party-size validation.
- Mobile-number validation.
- Large-party enquiry behavior.
- Stable ticket-code behavior.
- Guest cancellation.
- Staff notification.
- Return-by-time display.
- Overdue notification display.
- Compatible table seating.
- Rejection of seating at an occupied table.
- Rejection of seating at an unsuitable table.
- Completion releasing a table.
- Use of the service layer rather than direct backend calls.

Do not spend time implementing exhaustive tests for every visual detail.

# Execution rule

Do not ask clarification questions about:

- Architecture.
- Integrations.
- Authentication.
- Persistence.
- Notifications.
- Logo uploads.
- Reservations.
- Venues.
- AI features.
- Backend implementation.

The decisions in this prompt are final for the prototype.

If something is ambiguous, choose the smallest reasonable mocked frontend behavior, document the assumption briefly in the README, and continue building.

Do not spend credits on speculative features, backend implementation, production integrations, or additional planning.

Prioritize, in this order:

1. A complete interactive guest flow.
2. A complete interactive staff flow.
3. A clean replaceable service layer.
4. A focused test suite.
5. A coherent responsive design.

# Deliverables

At the end:

1. The frontend runs in the Lovable preview.
2. The guest join flow is interactive.
3. The guest status and cancellation flow is interactive.
4. The staff dashboard is interactive.
5. Staff can notify and seat guests.
6. Large-party enquiries work through the mock service.
7. Overdue notified entries are visually clear.
8. All backend-related behavior goes through the mock service layer.
9. The service interface is clear enough to become the basis for a later OpenAPI contract.
10. Add a short README section explaining:
   - This is a frontend prototype.
   - Backend calls are mocked.
   - The service layer will later be replaced with a FastAPI client.
   - No real messages are sent.
   - Real logo upload is deferred to the backend phase.

Do not add features beyond this request. Prioritize a complete, coherent prototype over extra polish or speculative functionality.