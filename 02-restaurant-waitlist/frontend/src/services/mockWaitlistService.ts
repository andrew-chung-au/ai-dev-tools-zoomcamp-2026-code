/**
 * In-memory mock implementation of the backend-shaped WaitlistService.
 * No network, no database, no external SDKs. All business rules live here.
 */
import {
  classifyPartySize,
  isNeedsAttention,
  type ActivityEvent,
  type CreateGuestEntryRequest,
  type CreateGuestEntryResult,
  type DashboardData,
  type GuestStatus,
  type LargePartyEnquiry,
  type LargePartyEnquiryRequest,
  type LoginRequest,
  type Notification,
  type NotificationChannel,
  type NotificationRecipientType,
  type NotificationResult,
  type NotificationTemplateType,
  type PartySizeClass,
  type SeatEntryRequest,
  type StaffSession,
  type Table,
  type UpdateVenueRequest,
  type Venue,
  type WaitlistEntry,
  type WaitlistFilters,
  type WaitlistService,
  type WaitlistStatus,
} from "./waitlistService";

const MOBILE_PATTERN = /^\+?[0-9][0-9\s-]{6,17}$/;

export class MockServiceError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.name = "MockServiceError";
    this.code = code;
  }
}

let idCounter = 0;
const nextId = (prefix: string) => `${prefix}_${(++idCounter).toString().padStart(4, "0")}`;

const delay = (ms = 260) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const isoDate = (d: Date) => d.toISOString().slice(0, 10);
const minutesFromNow = (m: number) => new Date(Date.now() + m * 60_000).toISOString();

function pad3(n: number) {
  return n.toString().padStart(3, "0");
}

interface MockState {
  venue: Venue;
  tables: Table[];
  entries: WaitlistEntry[];
  enquiries: LargePartyEnquiry[];
  notifications: Notification[];
  activity: ActivityEvent[];
  sequenceByDate: Record<string, number>;
}

function createSeedState(): MockState {
  const today = isoDate(new Date());

  const venue: Venue = {
    id: "venue_demo",
    name: "Demo Restaurant",
    logoPlaceholderLabel: "Demo Restaurant logo placeholder",
    contactPhone: "+61 2 5550 0100",
    staffNotificationEmail: "front-of-house@demo-restaurant.example",
    menuUrl: "https://example.com/demo-restaurant/menu",
    maxOnlinePartySize: 12,
    gracePeriodMinutes: 10,
    entryMode: "staff_review",
    waitlistOpen: true,
    defaultWaitEstimateMinutes: { A: 15, B: 25, C: 40, D: 55 },
    serviceDate: today,
    messages: {
      joinMessage:
        "Join tonight's walk-in waitlist. We'll text you when your table is ready.",
      policyAcknowledgementMessage:
        "Wait times are estimates, not guaranteed seating times. Please stay nearby — after we notify you, we hold your table for the grace period only.",
      confirmationMessage:
        "You're on the waitlist. Keep this page open to see your ticket and status.",
      tableReadyMessage:
        "Your table is ready. Please come to the host stand and show your ticket code.",
      cancellationMessage:
        "Your waitlist entry has been cancelled. You're welcome to join again any time.",
      closedWaitlistMessage:
        "Our waitlist is closed right now. Please call us or try again during service hours.",
      largePartyMessage:
        "For parties larger than 12, please contact the restaurant so we can discuss seating options. Your request has not been added to the waitlist.",
      largePartyConfirmationMessage:
        "Thanks. We have sent your large-party request to the restaurant. A staff member will contact you to discuss available options. This request is not a confirmed booking or waitlist ticket.",
    },
  };

  const tables: Table[] = [
    { id: "tbl_1", name: "T1", capacity: 2, occupied: false, occupyingTicketCode: null, occupyingEntryId: null },
    { id: "tbl_2", name: "T2", capacity: 2, occupied: false, occupyingTicketCode: null, occupyingEntryId: null },
    { id: "tbl_3", name: "T3", capacity: 4, occupied: false, occupyingTicketCode: null, occupyingEntryId: null },
    { id: "tbl_4", name: "T4", capacity: 4, occupied: false, occupyingTicketCode: null, occupyingEntryId: null },
    { id: "tbl_5", name: "T5", capacity: 6, occupied: false, occupyingTicketCode: null, occupyingEntryId: null },
    { id: "tbl_6", name: "T6", capacity: 6, occupied: false, occupyingTicketCode: null, occupyingEntryId: null },
  ];

  const state: MockState = {
    venue,
    tables,
    entries: [],
    enquiries: [],
    notifications: [],
    activity: [],
    sequenceByDate: {},
  };

  const makeEntry = (opts: {
    guestName: string;
    partySize: number;
    originalPartySize?: number;
    mobileNumber: string;
    seatingNote?: string | null;
    status: WaitlistStatus;
    arrivalMinutesAgo: number;
    notifiedMinutesAgo?: number;
    tableId?: string;
  }): WaitlistEntry => {
    const seq = (state.sequenceByDate[today] ?? 0) + 1;
    state.sequenceByDate[today] = seq;
    const originalPartySize = opts.originalPartySize ?? opts.partySize;
    const originalClass = classifyPartySize(originalPartySize);
    const currentClass = classifyPartySize(opts.partySize);
    const notifiedAt =
      opts.notifiedMinutesAgo !== undefined ? minutesFromNow(-opts.notifiedMinutesAgo) : null;
    const table = opts.tableId ? state.tables.find((t) => t.id === opts.tableId)! : null;
    const entry: WaitlistEntry = {
      id: nextId("entry"),
      venueId: venue.id,
      serviceDate: today,
      ticketCode: `${originalClass}-${pad3(seq)}`,
      ticketSequence: seq,
      guestName: opts.guestName,
      partySize: opts.partySize,
      originalPartySize,
      originalPartyClass: originalClass,
      currentSeatingClass: currentClass,
      reviewRequired: originalClass !== currentClass,
      reviewReason:
        originalClass !== currentClass
          ? `Party size changed from ${originalPartySize} to ${opts.partySize}; seating class is now ${currentClass}.`
          : null,
      mobileNumber: opts.mobileNumber,
      seatingNote: opts.seatingNote ?? null,
      status: opts.status,
      arrivalTime: minutesFromNow(-opts.arrivalMinutesAgo),
      estimatedWaitMinutes: venue.defaultWaitEstimateMinutes[currentClass],
      notifiedAt,
      returnByAt:
        notifiedAt !== null
          ? new Date(new Date(notifiedAt).getTime() + venue.gracePeriodMinutes * 60_000).toISOString()
          : null,
      seatedAt: opts.status === "seated" ? minutesFromNow(-opts.arrivalMinutesAgo + 5) : null,
      completedAt: null,
      cancelledAt: null,
      tableId: table?.id ?? null,
      tableName: table?.name ?? null,
      seatingOverrideReason: null,
      accessToken: `tok_${Math.random().toString(36).slice(2, 10)}${seq}`,
    };
    if (table) {
      table.occupied = true;
      table.occupyingEntryId = entry.id;
      table.occupyingTicketCode = entry.ticketCode;
    }
    state.entries.push(entry);
    return entry;
  };

  makeEntry({
    guestName: "Ava Lindqvist",
    partySize: 2,
    mobileNumber: "+61 400 111 222",
    status: "waiting",
    arrivalMinutesAgo: 32,
  });
  const notified = makeEntry({
    guestName: "Marco Feld",
    partySize: 4,
    mobileNumber: "+61 400 333 444",
    seatingNote: "Prefers a booth",
    status: "notified",
    arrivalMinutesAgo: 28,
    notifiedMinutesAgo: 3,
  });
  makeEntry({
    guestName: "The Okonkwo Party",
    partySize: 6,
    mobileNumber: "+61 400 555 666",
    seatingNote: "Wheelchair access required",
    status: "waiting",
    arrivalMinutesAgo: 21,
  });
  const overdue = makeEntry({
    guestName: "Priya Raman",
    partySize: 3,
    mobileNumber: "+61 400 777 888",
    status: "notified",
    arrivalMinutesAgo: 45,
    notifiedMinutesAgo: 18,
  });
  makeEntry({
    guestName: "Tomas Berg",
    partySize: 5,
    originalPartySize: 3,
    mobileNumber: "+61 400 999 000",
    seatingNote: "Two extra guests arrived",
    status: "waiting",
    arrivalMinutesAgo: 14,
  });
  makeEntry({
    guestName: "Hannah Cole",
    partySize: 2,
    mobileNumber: "+61 401 222 333",
    status: "pending",
    arrivalMinutesAgo: 4,
  });
  makeEntry({
    guestName: "Diego Salas",
    partySize: 6,
    mobileNumber: "+61 401 444 555",
    status: "seated",
    arrivalMinutesAgo: 60,
    tableId: "tbl_5",
  });

  state.notifications.push({
    id: nextId("notif"),
    entryId: notified.id,
    recipientType: "guest",
    channel: "sms",
    templateType: "table_ready",
    renderedMessage: venue.messages.tableReadyMessage,
    deliveryStatus: "sent",
    createdAt: notified.notifiedAt!,
    sentAt: notified.notifiedAt!,
    errorMessage: null,
  });
  state.notifications.push({
    id: nextId("notif"),
    entryId: overdue.id,
    recipientType: "guest",
    channel: "sms",
    templateType: "table_ready",
    renderedMessage: venue.messages.tableReadyMessage,
    deliveryStatus: "sent",
    createdAt: overdue.notifiedAt!,
    sentAt: overdue.notifiedAt!,
    errorMessage: null,
  });

  return state;
}

const STATUS_RANK: Record<WaitlistStatus, number> = {
  notified: 0,
  pending: 1,
  waiting: 2,
  seated: 3,
  completed: 4,
  no_show: 5,
  cancelled: 6,
};

export class MockWaitlistService implements WaitlistService {
  private state: MockState;

  constructor() {
    this.state = createSeedState();
  }

  /** Test helper: restore seeded data. */
  reset() {
    this.state = createSeedState();
  }

  private findEntry(entryId: string): WaitlistEntry {
    const entry = this.state.entries.find((e) => e.id === entryId);
    if (!entry) throw new MockServiceError("entry_not_found", "Waitlist entry not found.");
    return entry;
  }

  private logActivity(entryId: string | null, type: string, description: string) {
    this.state.activity.push({
      id: nextId("act"),
      entryId,
      type,
      description,
      createdAt: new Date().toISOString(),
    });
  }

  private pushNotification(input: {
    entryId: string | null;
    recipientType: NotificationRecipientType;
    channel: NotificationChannel;
    templateType: NotificationTemplateType;
    renderedMessage: string;
  }): Notification {
    const now = new Date().toISOString();
    const notification: Notification = {
      id: nextId("notif"),
      entryId: input.entryId,
      recipientType: input.recipientType,
      channel: input.channel,
      templateType: input.templateType,
      renderedMessage: input.renderedMessage,
      deliveryStatus: "sent",
      createdAt: now,
      sentAt: now,
      errorMessage: null,
    };
    this.state.notifications.push(notification);
    return notification;
  }

  async login(input: LoginRequest): Promise<StaffSession> {
    await delay(320);
    if (!input.username.trim() || !input.password.trim()) {
      throw new MockServiceError("invalid_credentials", "Username and password are required.");
    }
    return {
      token: `mock_session_${Math.random().toString(36).slice(2, 12)}`,
      staffName: input.username.trim(),
      username: input.username.trim(),
      venueId: this.state.venue.id,
      issuedAt: new Date().toISOString(),
      mocked: true,
    };
  }

  async getVenue(): Promise<Venue> {
    await delay(180);
    return structuredClone(this.state.venue);
  }

  async updateVenue(input: UpdateVenueRequest): Promise<Venue> {
    await delay(320);
    const v = this.state.venue;
    if (input.name !== undefined) {
      if (!input.name.trim()) throw new MockServiceError("invalid_name", "Venue name is required.");
      v.name = input.name.trim();
    }
    if (input.contactPhone !== undefined) v.contactPhone = input.contactPhone;
    if (input.staffNotificationEmail !== undefined)
      v.staffNotificationEmail = input.staffNotificationEmail;
    if (input.menuUrl !== undefined) v.menuUrl = input.menuUrl;
    if (input.maxOnlinePartySize !== undefined) {
      if (!Number.isInteger(input.maxOnlinePartySize) || input.maxOnlinePartySize < 1)
        throw new MockServiceError(
          "invalid_max_party_size",
          "Maximum online party size must be a positive whole number.",
        );
      v.maxOnlinePartySize = input.maxOnlinePartySize;
    }
    if (input.gracePeriodMinutes !== undefined) {
      if (!Number.isInteger(input.gracePeriodMinutes) || input.gracePeriodMinutes < 1)
        throw new MockServiceError(
          "invalid_grace_period",
          "Grace period must be a positive whole number of minutes.",
        );
      v.gracePeriodMinutes = input.gracePeriodMinutes;
    }
    if (input.entryMode !== undefined) v.entryMode = input.entryMode;
    if (input.waitlistOpen !== undefined) v.waitlistOpen = input.waitlistOpen;
    if (input.defaultWaitEstimateMinutes) {
      for (const key of Object.keys(input.defaultWaitEstimateMinutes) as PartySizeClass[]) {
        const value = input.defaultWaitEstimateMinutes[key];
        if (value !== undefined) v.defaultWaitEstimateMinutes[key] = value;
      }
    }
    if (input.messages) v.messages = { ...v.messages, ...input.messages };
    return structuredClone(v);
  }

  async getDashboard(serviceDate?: string): Promise<DashboardData> {
    await delay(280);
    const date = serviceDate ?? this.state.venue.serviceDate;
    const entries = this.sortEntries(this.state.entries.filter((e) => e.serviceDate === date));
    return structuredClone({
      venue: this.state.venue,
      serviceDate: date,
      summary: {
        activeWaiting: entries.filter((e) => e.status === "waiting").length,
        pendingReview: entries.filter((e) => e.status === "pending").length,
        notified: entries.filter((e) => e.status === "notified").length,
        needsAttention: entries.filter((e) => isNeedsAttention(e)).length,
      },
      entries,
      tables: this.state.tables,
    });
  }

  private sortEntries(entries: WaitlistEntry[]): WaitlistEntry[] {
    return [...entries].sort((a, b) => {
      if (STATUS_RANK[a.status] !== STATUS_RANK[b.status])
        return STATUS_RANK[a.status] - STATUS_RANK[b.status];
      if (a.currentSeatingClass !== b.currentSeatingClass)
        return a.currentSeatingClass < b.currentSeatingClass ? -1 : 1;
      return new Date(a.arrivalTime).getTime() - new Date(b.arrivalTime).getTime();
    });
  }

  async listWaitlistEntries(filters: WaitlistFilters = {}): Promise<WaitlistEntry[]> {
    await delay(200);
    const date = filters.serviceDate ?? this.state.venue.serviceDate;
    let entries = this.state.entries.filter((e) => e.serviceDate === date);
    if (filters.status && filters.status !== "all")
      entries = entries.filter((e) => e.status === filters.status);
    if (filters.partySizeClass && filters.partySizeClass !== "all")
      entries = entries.filter((e) => e.currentSeatingClass === filters.partySizeClass);
    if (filters.reviewRequiredOnly) entries = entries.filter((e) => e.reviewRequired);
    if (filters.needsAttentionOnly) entries = entries.filter((e) => isNeedsAttention(e));
    return structuredClone(this.sortEntries(entries));
  }

  async createGuestEntry(input: CreateGuestEntryRequest): Promise<CreateGuestEntryResult> {
    await delay(360);
    const venue = this.state.venue;
    if (!venue.waitlistOpen) {
      return { kind: "closed", message: venue.messages.closedWaitlistMessage };
    }
    if (!input.policyAcknowledged)
      throw new MockServiceError(
        "policy_not_acknowledged",
        "You must acknowledge the waitlist policy before joining.",
      );
    if (!input.guestName.trim())
      throw new MockServiceError("invalid_name", "Please enter a name for the party.");
    if (!Number.isInteger(input.partySize) || input.partySize < 1)
      throw new MockServiceError(
        "invalid_party_size",
        "Party size must be a whole number of one or more.",
      );
    if (!MOBILE_PATTERN.test(input.mobileNumber.trim()))
      throw new MockServiceError(
        "invalid_mobile_number",
        "Please enter a valid mobile number, for example +61 400 000 000.",
      );

    if (input.partySize > venue.maxOnlinePartySize) {
      const enquiry = await this.createLargePartyEnquiry({
        guestName: input.guestName.trim(),
        partySize: input.partySize,
        mobileNumber: input.mobileNumber.trim(),
        note: input.seatingNote,
      });
      return {
        kind: "large_party_enquiry",
        enquiry,
        message: venue.messages.largePartyConfirmationMessage,
      };
    }

    const date = venue.serviceDate;
    const seq = (this.state.sequenceByDate[date] ?? 0) + 1;
    this.state.sequenceByDate[date] = seq;
    const partyClass = classifyPartySize(input.partySize);
    const entry: WaitlistEntry = {
      id: nextId("entry"),
      venueId: venue.id,
      serviceDate: date,
      ticketCode: `${partyClass}-${pad3(seq)}`,
      ticketSequence: seq,
      guestName: input.guestName.trim(),
      partySize: input.partySize,
      originalPartySize: input.partySize,
      originalPartyClass: partyClass,
      currentSeatingClass: partyClass,
      reviewRequired: false,
      reviewReason: null,
      mobileNumber: input.mobileNumber.trim(),
      seatingNote: input.seatingNote?.trim() ? input.seatingNote.trim() : null,
      status: venue.entryMode === "staff_review" ? "pending" : "waiting",
      arrivalTime: new Date().toISOString(),
      estimatedWaitMinutes: venue.defaultWaitEstimateMinutes[partyClass],
      notifiedAt: null,
      returnByAt: null,
      seatedAt: null,
      completedAt: null,
      cancelledAt: null,
      tableId: null,
      tableName: null,
      seatingOverrideReason: null,
      accessToken: `tok_${Math.random().toString(36).slice(2, 12)}`,
    };
    this.state.entries.push(entry);
    this.logActivity(entry.id, "entry_created", `${entry.ticketCode} joined the waitlist.`);
    this.pushNotification({
      entryId: entry.id,
      recipientType: "guest",
      channel: "in_app",
      templateType: "confirmation",
      renderedMessage: venue.messages.confirmationMessage,
    });
    return {
      kind: "entry",
      entry: structuredClone(entry),
      accessToken: entry.accessToken,
      message: venue.messages.confirmationMessage,
    };
  }

  private guestMessage(entry: WaitlistEntry): string {
    const m = this.state.venue.messages;
    switch (entry.status) {
      case "notified":
        return m.tableReadyMessage;
      case "cancelled":
        return m.cancellationMessage;
      case "seated":
        return `You're seated at ${entry.tableName ?? "your table"}. Enjoy your meal.`;
      case "completed":
        return "Thanks for dining with us today.";
      case "no_show":
        return "We weren't able to seat this party. Please talk to the host stand.";
      case "pending":
        return "Your request is with our host stand for review.";
      default:
        return m.confirmationMessage;
    }
  }

  async getGuestEntry(accessToken: string): Promise<GuestStatus> {
    await delay(220);
    const entry = this.state.entries.find((e) => e.accessToken === accessToken);
    if (!entry) throw new MockServiceError("entry_not_found", "We couldn't find this waitlist entry.");
    return {
      ticketCode: entry.ticketCode,
      guestName: entry.guestName,
      partySize: entry.partySize,
      status: entry.status,
      estimatedWaitMinutes: entry.estimatedWaitMinutes,
      message: this.guestMessage(entry),
      notifiedAt: entry.notifiedAt,
      returnByAt: entry.returnByAt,
      needsAttention: isNeedsAttention(entry),
      cancellationAllowed: ["pending", "waiting", "notified"].includes(entry.status),
      venueName: this.state.venue.name,
      venueLogoPlaceholderLabel: this.state.venue.logoPlaceholderLabel,
      serviceDate: entry.serviceDate,
    };
  }

  async cancelGuestEntry(accessToken: string): Promise<WaitlistEntry> {
    await delay(300);
    const entry = this.state.entries.find((e) => e.accessToken === accessToken);
    if (!entry) throw new MockServiceError("entry_not_found", "We couldn't find this waitlist entry.");
    if (!["pending", "waiting", "notified"].includes(entry.status))
      throw new MockServiceError(
        "cancellation_not_allowed",
        "This entry can no longer be cancelled online.",
      );
    entry.status = "cancelled";
    entry.cancelledAt = new Date().toISOString();
    this.logActivity(entry.id, "guest_cancelled", `${entry.ticketCode} cancelled from the guest page.`);
    this.pushNotification({
      entryId: entry.id,
      recipientType: "staff",
      channel: "in_app",
      templateType: "cancellation",
      renderedMessage: `${entry.ticketCode} (${entry.guestName}) cancelled their waitlist entry.`,
    });
    return structuredClone(entry);
  }

  async approveEntry(entryId: string): Promise<WaitlistEntry> {
    await delay(240);
    const entry = this.findEntry(entryId);
    if (entry.status !== "pending")
      throw new MockServiceError("invalid_status", "Only pending entries can be approved.");
    entry.status = "waiting";
    this.logActivity(entry.id, "entry_approved", `${entry.ticketCode} approved onto the waitlist.`);
    return structuredClone(entry);
  }

  async cancelEntry(entryId: string): Promise<WaitlistEntry> {
    await delay(240);
    const entry = this.findEntry(entryId);
    if (["completed", "cancelled", "no_show"].includes(entry.status))
      throw new MockServiceError("invalid_status", "This entry is already closed.");
    this.releaseTable(entry);
    entry.status = "cancelled";
    entry.cancelledAt = new Date().toISOString();
    this.logActivity(entry.id, "staff_cancelled", `${entry.ticketCode} cancelled by staff.`);
    return structuredClone(entry);
  }

  async notifyEntry(entryId: string): Promise<NotificationResult> {
    await delay(280);
    const entry = this.findEntry(entryId);
    if (!["waiting", "notified"].includes(entry.status))
      throw new MockServiceError("invalid_status", "Only waiting guests can be notified.");
    const now = new Date();
    entry.status = "notified";
    entry.notifiedAt = now.toISOString();
    entry.returnByAt = new Date(
      now.getTime() + this.state.venue.gracePeriodMinutes * 60_000,
    ).toISOString();
    const notification = this.pushNotification({
      entryId: entry.id,
      recipientType: "guest",
      channel: "sms",
      templateType: "table_ready",
      renderedMessage: this.state.venue.messages.tableReadyMessage,
    });
    this.logActivity(entry.id, "guest_notified", `${entry.ticketCode} notified that a table is ready.`);
    return { entry: structuredClone(entry), notification: structuredClone(notification) };
  }

  async returnToWaiting(entryId: string): Promise<WaitlistEntry> {
    await delay(200);
    const entry = this.findEntry(entryId);
    if (entry.status !== "notified")
      throw new MockServiceError("invalid_status", "Only notified entries can return to waiting.");
    entry.status = "waiting";
    entry.notifiedAt = null;
    entry.returnByAt = null;
    this.logActivity(entry.id, "returned_to_waiting", `${entry.ticketCode} returned to waiting.`);
    return structuredClone(entry);
  }

  async extendReturnBy(entryId: string, additionalMinutes: number): Promise<WaitlistEntry> {
    await delay(200);
    const entry = this.findEntry(entryId);
    if (entry.status !== "notified" || !entry.returnByAt)
      throw new MockServiceError("invalid_status", "Only notified entries have a return-by time.");
    entry.returnByAt = new Date(
      new Date(entry.returnByAt).getTime() + additionalMinutes * 60_000,
    ).toISOString();
    this.logActivity(
      entry.id,
      "return_by_extended",
      `${entry.ticketCode} return-by extended by ${additionalMinutes} minutes.`,
    );
    return structuredClone(entry);
  }

  async updateWaitEstimate(entryId: string, estimatedWaitMinutes: number): Promise<WaitlistEntry> {
    await delay(200);
    const entry = this.findEntry(entryId);
    if (!Number.isInteger(estimatedWaitMinutes) || estimatedWaitMinutes < 0)
      throw new MockServiceError(
        "invalid_estimate",
        "Estimated wait must be a whole number of minutes.",
      );
    entry.estimatedWaitMinutes = estimatedWaitMinutes;
    this.logActivity(
      entry.id,
      "estimate_updated",
      `${entry.ticketCode} estimate set to ${estimatedWaitMinutes} minutes.`,
    );
    return structuredClone(entry);
  }

  private releaseTable(entry: WaitlistEntry) {
    if (!entry.tableId) return;
    const table = this.state.tables.find((t) => t.id === entry.tableId);
    if (table) {
      table.occupied = false;
      table.occupyingEntryId = null;
      table.occupyingTicketCode = null;
    }
  }

  async seatEntry(entryId: string, input: SeatEntryRequest): Promise<WaitlistEntry> {
    await delay(300);
    const entry = this.findEntry(entryId);
    if (["cancelled", "no_show", "completed", "seated"].includes(entry.status))
      throw new MockServiceError("invalid_status", "This entry cannot be seated.");
    const table = this.state.tables.find((t) => t.id === input.tableId);
    if (!table) throw new MockServiceError("table_not_found", "That table does not exist.");
    if (table.occupied)
      throw new MockServiceError("table_occupied", `${table.name} is already occupied.`);
    if (table.capacity < entry.partySize)
      throw new MockServiceError(
        "table_too_small",
        `${table.name} seats ${table.capacity} and this party is ${entry.partySize}.`,
      );
    entry.status = "seated";
    entry.seatedAt = new Date().toISOString();
    entry.tableId = table.id;
    entry.tableName = table.name;
    entry.seatingOverrideReason = input.seatingOverrideReason?.trim() || null;
    table.occupied = true;
    table.occupyingEntryId = entry.id;
    table.occupyingTicketCode = entry.ticketCode;
    this.logActivity(entry.id, "seated", `${entry.ticketCode} seated at ${table.name}.`);
    return structuredClone(entry);
  }

  async markNoShow(entryId: string): Promise<WaitlistEntry> {
    await delay(240);
    const entry = this.findEntry(entryId);
    if (entry.status !== "notified")
      throw new MockServiceError("invalid_status", "Only notified guests can be marked no-show.");
    entry.status = "no_show";
    this.logActivity(entry.id, "no_show", `${entry.ticketCode} marked as a no-show.`);
    return structuredClone(entry);
  }

  async completeEntry(entryId: string): Promise<WaitlistEntry> {
    await delay(240);
    const entry = this.findEntry(entryId);
    if (entry.status !== "seated")
      throw new MockServiceError("invalid_status", "Only seated parties can be completed.");
    this.releaseTable(entry);
    entry.status = "completed";
    entry.completedAt = new Date().toISOString();
    this.logActivity(entry.id, "completed", `${entry.ticketCode} completed; table released.`);
    return structuredClone(entry);
  }

  async listTables(): Promise<Table[]> {
    await delay(180);
    return structuredClone(this.state.tables);
  }

  async listCompatibleTables(entryId: string): Promise<Table[]> {
    await delay(150);
    const entry = this.findEntry(entryId);
    return structuredClone(
      this.state.tables.filter((t) => !t.occupied && t.capacity >= entry.partySize),
    );
  }

  async createLargePartyEnquiry(input: LargePartyEnquiryRequest): Promise<LargePartyEnquiry> {
    await delay(280);
    if (!input.guestName.trim())
      throw new MockServiceError("invalid_name", "Please enter a name for the party.");
    if (!MOBILE_PATTERN.test(input.mobileNumber.trim()))
      throw new MockServiceError("invalid_mobile_number", "Please enter a valid mobile number.");
    const enquiry: LargePartyEnquiry = {
      id: nextId("enq"),
      reference: `LP-${(this.state.enquiries.length + 1).toString().padStart(3, "0")}`,
      venueId: this.state.venue.id,
      guestName: input.guestName.trim(),
      partySize: input.partySize,
      mobileNumber: input.mobileNumber.trim(),
      note: input.note?.trim() ? input.note.trim() : null,
      createdAt: new Date().toISOString(),
      message: this.state.venue.messages.largePartyConfirmationMessage,
    };
    this.state.enquiries.push(enquiry);
    this.pushNotification({
      entryId: null,
      recipientType: "staff",
      channel: "in_app",
      templateType: "large_party_staff_alert",
      renderedMessage: `Large-party enquiry ${enquiry.reference}: ${enquiry.guestName}, party of ${enquiry.partySize}.`,
    });
    this.logActivity(null, "large_party_enquiry", `Large-party enquiry ${enquiry.reference} created.`);
    return structuredClone(enquiry);
  }

  async listNotifications(): Promise<Notification[]> {
    await delay(150);
    return structuredClone([...this.state.notifications].reverse());
  }

  async createNotificationEvent(input: {
    entryId: string | null;
    recipientType: NotificationRecipientType;
    channel: NotificationChannel;
    templateType: NotificationTemplateType;
    renderedMessage: string;
  }): Promise<Notification> {
    await delay(120);
    return structuredClone(this.pushNotification(input));
  }
}
