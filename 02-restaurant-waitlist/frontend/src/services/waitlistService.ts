/**
 * Backend-shaped service contract for the waitlist prototype.
 *
 * These types are intentionally explicit and serializable: a later phase will
 * translate them into an OpenAPI contract and a FastAPI backend. React code
 * must only ever talk to the `WaitlistService` interface.
 */

export type PartySizeClass = "A" | "B" | "C" | "D";

export type WaitlistStatus =
  | "pending"
  | "waiting"
  | "notified"
  | "seated"
  | "completed"
  | "cancelled"
  | "no_show";

export type EntryMode = "automatic" | "staff_review";

export interface VenueMessageSettings {
  joinMessage: string;
  policyAcknowledgementMessage: string;
  confirmationMessage: string;
  tableReadyMessage: string;
  cancellationMessage: string;
  closedWaitlistMessage: string;
  largePartyMessage: string;
  largePartyConfirmationMessage: string;
}

export interface Venue {
  id: string;
  name: string;
  logoPlaceholderLabel: string;
  contactPhone: string;
  staffNotificationEmail: string;
  menuUrl: string;
  maxOnlinePartySize: number;
  gracePeriodMinutes: number;
  entryMode: EntryMode;
  waitlistOpen: boolean;
  defaultWaitEstimateMinutes: Record<PartySizeClass, number>;
  messages: VenueMessageSettings;
  serviceDate: string; // YYYY-MM-DD
}

export interface StaffSession {
  token: string;
  staffName: string;
  username: string;
  venueId: string;
  issuedAt: string;
  mocked: true;
}

export type TableAvailabilityState = "available" | "occupied" | "needs_tidying";

export interface Table {
  id: string;
  name: string;
  minCapacity: number;
  maxCapacity: number;
  active: boolean;
  availabilityState: TableAvailabilityState;
  notes: string | null;
  occupyingTicketCode: string | null;
  occupyingEntryId: string | null;
}

export interface CreateTableRequest {
  name: string;
  minCapacity: number;
  maxCapacity: number;
  notes?: string | undefined;
}

export interface UpdateTableRequest {
  name?: string;
  minCapacity?: number;
  maxCapacity?: number;
  active?: boolean;
  notes?: string | null;
}

export interface SetTableAvailabilityRequest {
  availabilityState: "available" | "needs_tidying";
}

export interface WaitlistEntry {
  id: string;
  venueId: string;
  serviceDate: string;
  ticketCode: string;
  ticketSequence: number;
  guestName: string;
  partySize: number;
  originalPartySize: number;
  originalPartyClass: PartySizeClass;
  currentSeatingClass: PartySizeClass;
  reviewRequired: boolean;
  reviewReason: string | null;
  mobileNumber: string;
  seatingNote: string | null;
  status: WaitlistStatus;
  arrivalTime: string;
  estimatedWaitMinutes: number;
  notifiedAt: string | null;
  returnByAt: string | null;
  seatedAt: string | null;
  completedAt: string | null;
  cancelledAt: string | null;
  tableId: string | null;
  tableName: string | null;
  seatingOverrideReason: string | null;
  accessToken: string;
}

export interface LargePartyEnquiry {
  id: string;
  reference: string;
  venueId: string;
  guestName: string;
  partySize: number;
  mobileNumber: string;
  note: string | null;
  createdAt: string;
  message: string;
}

export type NotificationChannel = "sms" | "email" | "in_app";
export type NotificationRecipientType = "guest" | "staff";
export type NotificationTemplateType =
  | "table_ready"
  | "confirmation"
  | "cancellation"
  | "large_party_staff_alert";
export type NotificationDeliveryStatus = "queued" | "sent" | "failed";

export interface Notification {
  id: string;
  entryId: string | null;
  recipientType: NotificationRecipientType;
  channel: NotificationChannel;
  templateType: NotificationTemplateType;
  renderedMessage: string;
  deliveryStatus: NotificationDeliveryStatus;
  createdAt: string;
  sentAt: string | null;
  errorMessage: string | null;
}

export interface ActivityEvent {
  id: string;
  entryId: string | null;
  type: string;
  description: string;
  createdAt: string;
}

export interface WaitlistFilters {
  status?: WaitlistStatus | "all";
  partySizeClass?: PartySizeClass | "all";
  reviewRequiredOnly?: boolean;
  needsAttentionOnly?: boolean;
  serviceDate?: string;
}

export interface CreateGuestEntryRequest {
  guestName: string;
  partySize: number;
  mobileNumber: string;
  seatingNote?: string | undefined;
  policyAcknowledged: boolean;
}

export type CreateGuestEntryResult =
  | {
      kind: "entry";
      entry: WaitlistEntry;
      accessToken: string;
      message: string;
    }
  | {
      kind: "large_party_enquiry";
      enquiry: LargePartyEnquiry;
      message: string;
    }
  | {
      kind: "closed";
      message: string;
    };

export interface GuestStatus {
  ticketCode: string;
  guestName: string;
  partySize: number;
  status: WaitlistStatus;
  estimatedWaitMinutes: number;
  message: string;
  notifiedAt: string | null;
  returnByAt: string | null;
  needsAttention: boolean;
  cancellationAllowed: boolean;
  venueName: string;
  venueLogoPlaceholderLabel: string;
  serviceDate: string;
}

export interface SeatEntryRequest {
  tableId: string;
  seatingOverrideReason?: string | undefined;
}

export interface UpdateVenueRequest {
  name?: string;
  contactPhone?: string;
  staffNotificationEmail?: string;
  menuUrl?: string;
  maxOnlinePartySize?: number;
  gracePeriodMinutes?: number;
  entryMode?: EntryMode;
  waitlistOpen?: boolean;
  defaultWaitEstimateMinutes?: Partial<Record<PartySizeClass, number>>;
  messages?: Partial<VenueMessageSettings>;
}

export interface NotificationResult {
  entry: WaitlistEntry;
  notification: Notification;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LargePartyEnquiryRequest {
  guestName: string;
  partySize: number;
  mobileNumber: string;
  note?: string | undefined;
}

export interface DashboardSummary {
  activeWaiting: number;
  pendingReview: number;
  notified: number;
  needsAttention: number;
}

export interface DashboardData {
  venue: Venue;
  serviceDate: string;
  summary: DashboardSummary;
  entries: WaitlistEntry[];
  tables: Table[];
}

export interface ServiceError extends Error {
  code: string;
}

export interface WaitlistService {
  login(input: LoginRequest): Promise<StaffSession>;
  getVenue(): Promise<Venue>;
  updateVenue(input: UpdateVenueRequest): Promise<Venue>;
  getDashboard(serviceDate?: string): Promise<DashboardData>;
  listWaitlistEntries(filters?: WaitlistFilters): Promise<WaitlistEntry[]>;
  createGuestEntry(input: CreateGuestEntryRequest): Promise<CreateGuestEntryResult>;
  getGuestEntry(accessToken: string): Promise<GuestStatus>;
  cancelGuestEntry(accessToken: string): Promise<WaitlistEntry>;
  approveEntry(entryId: string): Promise<WaitlistEntry>;
  cancelEntry(entryId: string): Promise<WaitlistEntry>;
  notifyEntry(entryId: string): Promise<NotificationResult>;
  returnToWaiting(entryId: string): Promise<WaitlistEntry>;
  extendReturnBy(entryId: string, additionalMinutes: number): Promise<WaitlistEntry>;
  updateWaitEstimate(entryId: string, estimatedWaitMinutes: number): Promise<WaitlistEntry>;
  seatEntry(entryId: string, input: SeatEntryRequest): Promise<WaitlistEntry>;
  markNoShow(entryId: string): Promise<WaitlistEntry>;
  completeEntry(entryId: string): Promise<WaitlistEntry>;
  listTables(): Promise<Table[]>;
  listCompatibleTables(entryId: string): Promise<Table[]>;
  createTable(input: CreateTableRequest): Promise<Table>;
  updateTable(tableId: string, input: UpdateTableRequest): Promise<Table>;
  deleteTable(tableId: string): Promise<void>;
  setTableAvailability(tableId: string, input: SetTableAvailabilityRequest): Promise<Table>;
  createLargePartyEnquiry(input: LargePartyEnquiryRequest): Promise<LargePartyEnquiry>;
  listNotifications(): Promise<Notification[]>;
  createNotificationEvent(input: {
    entryId: string | null;
    recipientType: NotificationRecipientType;
    channel: NotificationChannel;
    templateType: NotificationTemplateType;
    renderedMessage: string;
  }): Promise<Notification>;
}

export function classifyPartySize(partySize: number): PartySizeClass {
  if (partySize <= 2) return "A";
  if (partySize <= 4) return "B";
  if (partySize <= 6) return "C";
  return "D";
}

export function isNeedsAttention(entry: WaitlistEntry, now: Date = new Date()): boolean {
  return (
    entry.status === "notified" &&
    entry.returnByAt !== null &&
    new Date(entry.returnByAt).getTime() < now.getTime()
  );
}

export const PARTY_CLASS_LABELS: Record<PartySizeClass, string> = {
  A: "A (1-2)",
  B: "B (3-4)",
  C: "C (5-6)",
  D: "D (7-12)",
};

export const STATUS_LABELS: Record<WaitlistStatus, string> = {
  pending: "Pending review",
  waiting: "Waiting",
  notified: "Notified",
  seated: "Seated",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No show",
};
