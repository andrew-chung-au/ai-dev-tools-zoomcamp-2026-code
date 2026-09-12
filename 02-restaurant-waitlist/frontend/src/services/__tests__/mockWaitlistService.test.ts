import { beforeEach, describe, expect, it } from "vitest";
import { MockWaitlistService } from "../mockWaitlistService";
import { isNeedsAttention, type WaitlistService } from "../waitlistService";
import { waitlistService } from "../index";

let service: MockWaitlistService;

const validGuest = {
  guestName: "Test Guest",
  partySize: 2,
  mobileNumber: "+61 400 123 456",
  policyAcknowledged: true,
};

beforeEach(() => {
  service = new MockWaitlistService();
});

describe("guest join", () => {
  it("accepts a valid submission and issues a ticket via the service", async () => {
    const result = await service.createGuestEntry(validGuest);
    expect(result.kind).toBe("entry");
    if (result.kind !== "entry") return;
    expect(result.entry.ticketCode).toMatch(/^[ABCD]-\d{3}$/);
    expect(result.accessToken).toBeTruthy();
  });

  it("requires policy acknowledgement", async () => {
    await expect(
      service.createGuestEntry({ ...validGuest, policyAcknowledged: false }),
    ).rejects.toMatchObject({ code: "policy_not_acknowledged" });
  });

  it("requires a name", async () => {
    await expect(service.createGuestEntry({ ...validGuest, guestName: "  " })).rejects.toMatchObject({
      code: "invalid_name",
    });
  });

  it("validates party size", async () => {
    await expect(service.createGuestEntry({ ...validGuest, partySize: 0 })).rejects.toMatchObject({
      code: "invalid_party_size",
    });
    await expect(service.createGuestEntry({ ...validGuest, partySize: 2.5 })).rejects.toMatchObject({
      code: "invalid_party_size",
    });
  });

  it("validates the mobile number", async () => {
    await expect(
      service.createGuestEntry({ ...validGuest, mobileNumber: "abc" }),
    ).rejects.toMatchObject({ code: "invalid_mobile_number" });
  });

  it("creates a large-party enquiry instead of a ticket above the maximum", async () => {
    const result = await service.createGuestEntry({ ...validGuest, partySize: 20 });
    expect(result.kind).toBe("large_party_enquiry");
    if (result.kind !== "large_party_enquiry") return;
    expect(result.enquiry.reference).toMatch(/^LP-\d{3}$/);
    const staffAlerts = (await service.listNotifications()).filter(
      (n) => n.templateType === "large_party_staff_alert",
    );
    expect(staffAlerts.length).toBe(1);
  });

  it("blocks submissions while the waitlist is closed", async () => {
    await service.updateVenue({ waitlistOpen: false });
    const result = await service.createGuestEntry(validGuest);
    expect(result.kind).toBe("closed");
  });
});

describe("tickets", () => {
  it("uses one shared sequence and keeps ticket codes stable", async () => {
    const first = await service.createGuestEntry(validGuest);
    const second = await service.createGuestEntry({ ...validGuest, partySize: 5 });
    if (first.kind !== "entry" || second.kind !== "entry") throw new Error("expected entries");
    expect(second.entry.ticketSequence).toBe(first.entry.ticketSequence + 1);

    const before = second.entry.ticketCode;
    await service.approveEntry(second.entry.id).catch(() => undefined);
    const entries = await service.listWaitlistEntries();
    const same = entries.find((e) => e.id === second.entry.id);
    expect(same?.ticketCode).toBe(before);
  });

  it("does not reuse a cancelled ticket number", async () => {
    const created = await service.createGuestEntry(validGuest);
    if (created.kind !== "entry") throw new Error("expected entry");
    await service.cancelEntry(created.entry.id);
    const next = await service.createGuestEntry(validGuest);
    if (next.kind !== "entry") throw new Error("expected entry");
    expect(next.entry.ticketSequence).toBe(created.entry.ticketSequence + 1);
  });

  it("flags seeded review-required entries with the original ticket class", async () => {
    const entries = await service.listWaitlistEntries({ reviewRequiredOnly: true });
    expect(entries.length).toBeGreaterThan(0);
    const entry = entries[0]!;
    expect(entry.ticketCode.startsWith(entry.originalPartyClass)).toBe(true);
    expect(entry.currentSeatingClass).not.toBe(entry.originalPartyClass);
    expect(entry.reviewReason).toBeTruthy();
  });
});

describe("guest cancellation", () => {
  it("cancels the entry through the access token", async () => {
    const created = await service.createGuestEntry(validGuest);
    if (created.kind !== "entry") throw new Error("expected entry");
    const cancelled = await service.cancelGuestEntry(created.accessToken);
    expect(cancelled.status).toBe("cancelled");
    const status = await service.getGuestEntry(created.accessToken);
    expect(status.cancellationAllowed).toBe(false);
    const waiting = await service.listWaitlistEntries({ status: "waiting" });
    expect(waiting.some((e) => e.id === created.entry.id)).toBe(false);
  });
});

describe("notifications", () => {
  it("notifies a waiting guest and records a return-by time", async () => {
    const entries = await service.listWaitlistEntries({ status: "waiting" });
    const target = entries[0]!;
    const { entry, notification } = await service.notifyEntry(target.id);
    expect(entry.status).toBe("notified");
    expect(entry.notifiedAt).toBeTruthy();
    expect(entry.returnByAt).toBeTruthy();
    expect(new Date(entry.returnByAt!).getTime()).toBeGreaterThan(
      new Date(entry.notifiedAt!).getTime(),
    );
    expect(notification.deliveryStatus).toBe("sent");
    expect(notification.templateType).toBe("table_ready");

    const status = await service.getGuestEntry(entry.accessToken);
    expect(status.status).toBe("notified");
    expect(status.returnByAt).toBe(entry.returnByAt);
  });

  it("marks an overdue notified entry as needing attention", async () => {
    const dashboard = await service.getDashboard();
    const overdue = dashboard.entries.find((e) => isNeedsAttention(e));
    expect(overdue).toBeDefined();
    expect(dashboard.summary.needsAttention).toBeGreaterThan(0);
    const status = await service.getGuestEntry(overdue!.accessToken);
    expect(status.needsAttention).toBe(true);
  });
});

describe("seating", () => {
  async function waitingEntry() {
    const entries = await service.listWaitlistEntries({ status: "waiting" });
    return entries[0]!;
  }

  it("seats a party at a compatible available table", async () => {
    const entry = (await waitingEntry())!;
    const compatible = await service.listCompatibleTables(entry.id);
    expect(compatible.length).toBeGreaterThan(0);
    const seated = await service.seatEntry(entry.id, { tableId: compatible[0]!.id });
    expect(seated.status).toBe("seated");
    const tables = await service.listTables();
    const table = tables.find((t) => t.id === compatible[0]!.id)!;
    expect(table.occupied).toBe(true);
    expect(table.occupyingTicketCode).toBe(seated.ticketCode);
  });

  it("rejects seating at an occupied table", async () => {
    const tables = await service.listTables();
    const occupied = tables.find((t) => t.occupied)!;
    const entry = (await waitingEntry())!;
    await expect(service.seatEntry(entry.id, { tableId: occupied.id })).rejects.toMatchObject({
      code: "table_occupied",
    });
  });

  it("rejects seating at a table with insufficient capacity", async () => {
    const entries = await service.listWaitlistEntries({ status: "waiting" });
    const bigParty = entries.find((e) => e.partySize > 2)!;
    const tables = await service.listTables();
    const small = tables.find((t) => t.capacity === 2 && !t.occupied)!;
    await expect(service.seatEntry(bigParty.id, { tableId: small.id })).rejects.toMatchObject({
      code: "table_too_small",
    });
  });

  it("releases the table when the party is completed", async () => {
    const entry = (await waitingEntry())!;
    const compatible = await service.listCompatibleTables(entry.id);
    const seated = await service.seatEntry(entry.id, { tableId: compatible[0]!.id });
    const completed = await service.completeEntry(seated.id);
    expect(completed.status).toBe("completed");
    const tables = await service.listTables();
    expect(tables.find((t) => t.id === compatible[0]!.id)!.occupied).toBe(false);
  });
});

describe("service layer", () => {
  it("exports a single active service implementing the interface", () => {
    const typed: WaitlistService = waitlistService;
    expect(typeof typed.createGuestEntry).toBe("function");
    expect(typeof typed.seatEntry).toBe("function");
  });

  it("does not use fetch or other network clients in the mock implementation", async () => {
    const source = await import("node:fs/promises").then((fs) =>
      fs.readFile(new URL("../mockWaitlistService.ts", import.meta.url), "utf8"),
    );
    expect(source).not.toMatch(/\bfetch\(/);
    expect(source).not.toMatch(/axios/);
    expect(source).not.toMatch(/supabase/i);
  });

  it("logs in with any non-empty mocked credentials and rejects empty ones", async () => {
    const session = await service.login({ username: "host", password: "demo" });
    expect(session.mocked).toBe(true);
    await expect(service.login({ username: "", password: "" })).rejects.toMatchObject({
      code: "invalid_credentials",
    });
  });
});
