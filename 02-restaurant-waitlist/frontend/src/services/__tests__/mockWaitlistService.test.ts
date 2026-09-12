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
    expect(table.availabilityState).toBe("occupied");
    expect(table.occupyingTicketCode).toBe(seated.ticketCode);
  });

  it("rejects seating at an occupied table", async () => {
    const tables = await service.listTables();
    const occupied = tables.find((t) => t.availabilityState === "occupied")!;
    const entry = (await waitingEntry())!;
    await expect(service.seatEntry(entry.id, { tableId: occupied.id })).rejects.toMatchObject({
      code: "table_occupied",
    });
  });

  it("rejects seating at an inactive table", async () => {
    const tables = await service.listTables();
    const inactive = tables.find((t) => !t.active)!;
    const entries = await service.listWaitlistEntries({ status: "waiting" });
    const compatibleParty = entries.find(
      (e) => e.partySize >= inactive.minCapacity && e.partySize <= inactive.maxCapacity,
    )!;
    await expect(
      service.seatEntry(compatibleParty.id, { tableId: inactive.id }),
    ).rejects.toMatchObject({ code: "table_inactive" });
  });

  it("rejects seating at a table that needs tidying", async () => {
    const tables = await service.listTables();
    const needsTidying = tables.find((t) => t.active && t.availabilityState === "needs_tidying")!;
    const entries = await service.listWaitlistEntries({ status: "waiting" });
    const compatibleParty = entries.find(
      (e) => e.partySize >= needsTidying.minCapacity && e.partySize <= needsTidying.maxCapacity,
    )!;
    await expect(
      service.seatEntry(compatibleParty.id, { tableId: needsTidying.id }),
    ).rejects.toMatchObject({ code: "table_not_available" });
  });

  it("rejects seating at a table with insufficient capacity", async () => {
    const entries = await service.listWaitlistEntries({ status: "waiting" });
    const bigParty = entries.find((e) => e.partySize > 2)!;
    const tables = await service.listTables();
    const small = tables.find((t) => t.maxCapacity === 2 && t.availabilityState === "available")!;
    await expect(service.seatEntry(bigParty.id, { tableId: small.id })).rejects.toMatchObject({
      code: "table_too_small",
    });
  });

  it("marks the table as needing tidying when the party is completed", async () => {
    const entry = (await waitingEntry())!;
    const compatible = await service.listCompatibleTables(entry.id);
    const seated = await service.seatEntry(entry.id, { tableId: compatible[0]!.id });
    const completed = await service.completeEntry(seated.id);
    expect(completed.status).toBe("completed");
    const tables = await service.listTables();
    const table = tables.find((t) => t.id === compatible[0]!.id)!;
    expect(table.availabilityState).toBe("needs_tidying");
    expect(table.occupyingEntryId).toBeNull();
  });
});

describe("table management", () => {
  it("creates a table with default availability and active state", async () => {
    const table = await service.createTable({ name: "T9", minCapacity: 2, maxCapacity: 4 });
    expect(table.active).toBe(true);
    expect(table.availabilityState).toBe("available");
    expect(table.notes).toBeNull();
  });

  it("rejects an invalid capacity range", async () => {
    await expect(
      service.createTable({ name: "T10", minCapacity: 4, maxCapacity: 2 }),
    ).rejects.toMatchObject({ code: "invalid_max_capacity" });
  });

  it("updates a table's name, capacities, active state and notes", async () => {
    const table = await service.createTable({ name: "T11", minCapacity: 2, maxCapacity: 4 });
    const updated = await service.updateTable(table.id, {
      name: "T11b",
      minCapacity: 3,
      maxCapacity: 5,
      active: false,
      notes: "Reserved for large parties",
    });
    expect(updated.name).toBe("T11b");
    expect(updated.minCapacity).toBe(3);
    expect(updated.maxCapacity).toBe(5);
    expect(updated.active).toBe(false);
    expect(updated.notes).toBe("Reserved for large parties");
  });

  it("deletes a table", async () => {
    const table = await service.createTable({ name: "T12", minCapacity: 2, maxCapacity: 4 });
    await service.deleteTable(table.id);
    const tables = await service.listTables();
    expect(tables.some((t) => t.id === table.id)).toBe(false);
  });

  it("refuses to delete an occupied table", async () => {
    const tables = await service.listTables();
    const occupied = tables.find((t) => t.availabilityState === "occupied")!;
    await expect(service.deleteTable(occupied.id)).rejects.toMatchObject({ code: "table_occupied" });
  });

  it("moves a needs_tidying table back to available", async () => {
    const tables = await service.listTables();
    const needsTidying = tables.find((t) => t.availabilityState === "needs_tidying")!;
    const updated = await service.setTableAvailability(needsTidying.id, {
      availabilityState: "available",
    });
    expect(updated.availabilityState).toBe("available");
  });

  it("does not allow marking an occupied table available directly", async () => {
    const tables = await service.listTables();
    const occupied = tables.find((t) => t.availabilityState === "occupied")!;
    await expect(
      service.setTableAvailability(occupied.id, { availabilityState: "available" }),
    ).rejects.toMatchObject({ code: "invalid_availability_transition" });
  });

  it("allows manually marking an occupied table as needing tidying", async () => {
    const tables = await service.listTables();
    const occupied = tables.find((t) => t.availabilityState === "occupied")!;
    const updated = await service.setTableAvailability(occupied.id, {
      availabilityState: "needs_tidying",
    });
    expect(updated.availabilityState).toBe("needs_tidying");
    expect(updated.occupyingEntryId).toBeNull();
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
