# User Acceptance Test (UAT) — Table Ready

This document describes how to manually test the full application end‑to‑end.  
Run these steps after starting both backend and frontend dev servers.

---

## 0. Prerequisites

From your local machine (with Bun/Node and Python/uv):

```bash
cd ~/courses/ai-dev-tools-zoomcamp-2026-code/02-restaurant-waitlist
```

Ensure you're on the commit you'll submit:

```bash
git log --oneline -1
```

---

## 1. Start backend and frontend

### Backend

In terminal 1:

```bash
cd ~/courses/ai-dev-tools-zoomcamp-2026-code/02-restaurant-waitlist
make run
```

You should see uvicorn starting on `http://localhost:8091`.

### Frontend

In terminal 2:

```bash
cd ~/courses/ai-dev-tools-zoomcamp-2026-code/02-restaurant-waitlist/frontend
bun run dev
```

Open your browser to:  
`http://localhost:8080`

Keep both terminals open while you run the tests below.

---

## 2. Guest flow (join, view status, cancel)

**Goal:** A guest can join the waitlist, see their status, and cancel.

1. On `http://localhost:8080`, go to the guest entry point (e.g. "Join waitlist" / guest page).
2. Enter:
   - Name: `Test Guest`
   - Party size: `2`
   - Any other required fields.
3. Submit the form.
   - **Expect:** a confirmation page with your entry details and a token/URL you can revisit.
4. Open the guest status page using the provided link/token.
   - **Expect:** you see your party size, position/status (e.g. `pending`).
5. On the guest status page, click "Cancel" (or equivalent).
   - **Expect:** confirmation that your entry is cancelled; status changes or page indicates cancellation.

Optional manual check via curl (no auth needed):

```bash
# After joining, note the entry token from the UI or logs, then:
curl http://localhost:8091/api/guest/entries/<TOKEN>
```

Expect a JSON object with your entry and a status field.

---

## 3. Staff login

**Goal:** Only valid staff credentials log in; others are rejected.

1. Navigate to the staff login page in the app.
2. Try invalid credentials, e.g.:
   - Username: `fake`
   - Password: `fake`
   - **Expect:** login fails with an error (401).
3. Log in with the seeded staff user:
   - Username: `manager`
   - Password: `waitlist123`
   - **Expect:** successful login and redirect to the staff dashboard.

Optional curl check:

```bash
# Wrong credentials
curl -X POST http://localhost:8091/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"fake","password":"fake"}'

# Correct credentials
curl -X POST http://localhost:8091/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"manager","password":"waitlist123"}'
```

The second call should return a 200 with a token.

---

## 4. Staff queue operations

**Goal:** Staff can see the queue, approve, notify, seat, and complete entries.

Do this while logged in as staff.

1. Ensure there is at least one pending entry (use the guest flow above if needed).
2. On the staff dashboard / queue page:
   - **Expect:** you see the pending entry with guest name and party size.
3. Approve the entry.
   - **Expect:** status changes to `approved` (or equivalent).
4. Notify the guest (if your UI has a "Notify" button).
   - **Expect:** status changes to `notified` (or similar).
5. Seat the guest:
   - Choose a table (e.g. `tbl_1`).
   - **Expect:** entry status becomes `seated` and the table shows as occupied.
6. Complete the seating:
   - Mark the table as finished / party left.
   - **Expect:** entry status becomes `completed` and the table becomes available again (or needs tidying, depending on your design).

Optional curl check (use the token from the guest entry and the token from staff login):

```bash
TOKEN=<ENTRY_TOKEN>
STAFF_TOKEN=<STAFF_BEARER_TOKEN>

# Approve
curl -X POST http://localhost:8091/api/waitlist-entries/$TOKEN/approve \
  -H "Authorization: Bearer $STAFF_TOKEN"

# Notify
curl -X POST http://localhost:8091/api/waitlist-entries/$TOKEN/notify \
  -H "Authorization: Bearer $STAFF_TOKEN"

# Seat at tbl_1
curl -X POST http://localhost:8091/api/waitlist-entries/$TOKEN/seat \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tableId":"tbl_1"}'

# Complete
curl -X POST http://localhost:8091/api/waitlist-entries/$TOKEN/complete \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

Each should return 200/204 and updated entry data where applicable.

---

## 5. Table management

**Goal:** Staff can create, update, deactivate, and delete tables.

While logged in as staff:

1. Go to the table management page.
2. Create a new table:
   - ID: `test-table`
   - Capacity: `4`
   - **Expect:** table appears in the list.
3. Deactivate the table (if your UI has an "active" toggle).
   - **Expect:** table is marked inactive / unavailable.
4. Delete the table.
   - **Expect:** table no longer appears in the list.

Optional curl check:

```bash
STAFF_TOKEN=<STAFF_BEARER_TOKEN>

# Create
curl -X POST http://localhost:8091/api/tables \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"test-table","capacity":4,"active":true}'

# Deactivate (PATCH active=false)
curl -X PATCH http://localhost:8091/api/tables/test-table \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"active":false}'

# Delete
curl -X DELETE http://localhost:8091/api/tables/test-table \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

Expect 201/200 for create/update and 204 for delete.

---

## 6. Large‑party enquiry

**Goal:** Oversized parties are redirected to a large‑party enquiry instead of joining the normal queue.

1. Determine your configured `maxOnlinePartySize` (check your backend config or docs; often 6 or 8).
2. On the guest join form, enter a party size larger than that limit, e.g. `10`.
3. Submit the form.
   - **Expect:** you are redirected to a large‑party enquiry page or shown a large‑party message.
   - **Expect:** a `LargePartyEnquiry` record is created (you can verify via API or UI if exposed).

Optional curl check:

```bash
curl -X POST http://localhost:8091/api/large-party-enquiries \
  -H "Content-Type: application/json" \
  -d '{"guestName":"Big Party","partySize":10,"notes":"UAT test"}'
```

Expect 201 with a `LargePartyEnquiry` object.

---

## 7. Venue settings & notifications (optional but nice)

**Goal:** Basic venue config and notifications endpoints work.

While logged in as staff:

1. Update venue settings (e.g. venue name, max online party size) via the UI if available.
   - **Expect:** changes are saved and reflected on subsequent loads.
2. View notifications list (if your UI exposes it).
   - **Expect:** you see a list (possibly empty) without errors.

Optional curl check:

```bash
STAFF_TOKEN=<STAFF_BEARER_TOKEN>

# Patch venue
curl -X PATCH http://localhost:8091/api/venue \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Venue"}'

# List notifications
curl http://localhost:8091/api/notifications \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

---

## 8. Run automated tests

After manual UAT, confirm tests still pass.

From `02-restaurant-waitlist`:

```bash
make test
```

**Expect:** all backend and frontend tests pass.

---

## Notes

- Replace `<TOKEN>` and `<STAFF_BEARER_TOKEN>` with actual values from your UI or login response.
- If any step fails, check browser console, terminal logs, and API responses for errors.
- This UAT assumes the default backend port `8091` and frontend dev server port `8080`.