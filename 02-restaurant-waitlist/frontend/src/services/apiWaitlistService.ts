/**
 * HTTP implementation of the backend-shaped WaitlistService, calling the
 * FastAPI backend described in `openapi.yaml`. No business rules live here;
 * they live in the backend. This file only translates between the
 * `WaitlistService` interface and HTTP requests/responses.
 */
import type {
  CreateGuestEntryRequest,
  CreateGuestEntryResult,
  CreateTableRequest,
  DashboardData,
  GuestStatus,
  LargePartyEnquiry,
  LargePartyEnquiryRequest,
  LoginRequest,
  Notification,
  NotificationChannel,
  NotificationRecipientType,
  NotificationResult,
  NotificationTemplateType,
  SeatEntryRequest,
  SetTableAvailabilityRequest,
  StaffSession,
  Table,
  UpdateTableRequest,
  UpdateVenueRequest,
  Venue,
  WaitlistEntry,
  WaitlistFilters,
  WaitlistService,
} from "./waitlistService";

/** Falls back to the backend's default local port (see backend/config.py). */
const DEFAULT_API_BASE_URL = "http://localhost:8091/api";

export class ApiServiceError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.name = "ApiServiceError";
    this.code = code;
  }
}

function resolveBaseUrl(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  return (configured || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
}

function toQueryString(params: Record<string, string | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export class ApiWaitlistService implements WaitlistService {
  private baseUrl: string;
  /** Staff bearer token, held in memory only; set on successful login. */
  private token: string | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? resolveBaseUrl();
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (init.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    } catch {
      throw new ApiServiceError(
        "network_error",
        "Could not reach the waitlist server. Check your connection and try again.",
      );
    }

    if (response.status === 204) return undefined as T;

    const payload: unknown = await response.json().catch(() => null);

    if (!response.ok) {
      const errorPayload = payload as { code?: string; message?: string } | null;
      throw new ApiServiceError(
        errorPayload?.code ?? "request_failed",
        errorPayload?.message ?? `Request failed with status ${response.status}.`,
      );
    }

    return payload as T;
  }

  async login(input: LoginRequest): Promise<StaffSession> {
    const session = await this.request<StaffSession>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    });
    this.token = session.token;
    return session;
  }

  async getVenue(): Promise<Venue> {
    return this.request<Venue>("/venue");
  }

  async updateVenue(input: UpdateVenueRequest): Promise<Venue> {
    return this.request<Venue>("/venue", { method: "PATCH", body: JSON.stringify(input) });
  }

  async getDashboard(serviceDate?: string): Promise<DashboardData> {
    return this.request<DashboardData>(`/dashboard${toQueryString({ serviceDate })}`);
  }

  async listWaitlistEntries(filters: WaitlistFilters = {}): Promise<WaitlistEntry[]> {
    const qs = toQueryString({
      status: filters.status,
      partySizeClass: filters.partySizeClass,
      reviewRequiredOnly: filters.reviewRequiredOnly,
      needsAttentionOnly: filters.needsAttentionOnly,
      serviceDate: filters.serviceDate,
    });
    return this.request<WaitlistEntry[]>(`/waitlist-entries${qs}`);
  }

  async createGuestEntry(input: CreateGuestEntryRequest): Promise<CreateGuestEntryResult> {
    return this.request<CreateGuestEntryResult>("/waitlist-entries", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async getGuestEntry(accessToken: string): Promise<GuestStatus> {
    return this.request<GuestStatus>(`/guest/entries/${encodeURIComponent(accessToken)}`);
  }

  async cancelGuestEntry(accessToken: string): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/guest/entries/${encodeURIComponent(accessToken)}/cancel`,
      { method: "POST" },
    );
  }

  async approveEntry(entryId: string): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/approve`,
      { method: "POST" },
    );
  }

  async cancelEntry(entryId: string): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(`/waitlist-entries/${encodeURIComponent(entryId)}/cancel`, {
      method: "POST",
    });
  }

  async notifyEntry(entryId: string): Promise<NotificationResult> {
    return this.request<NotificationResult>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/notify`,
      { method: "POST" },
    );
  }

  async returnToWaiting(entryId: string): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/return-to-waiting`,
      { method: "POST" },
    );
  }

  async extendReturnBy(entryId: string, additionalMinutes: number): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/extend-return-by`,
      { method: "POST", body: JSON.stringify({ additionalMinutes }) },
    );
  }

  async updateWaitEstimate(entryId: string, estimatedWaitMinutes: number): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/wait-estimate`,
      { method: "PATCH", body: JSON.stringify({ estimatedWaitMinutes }) },
    );
  }

  async seatEntry(entryId: string, input: SeatEntryRequest): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(`/waitlist-entries/${encodeURIComponent(entryId)}/seat`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async markNoShow(entryId: string): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/no-show`,
      { method: "POST" },
    );
  }

  async completeEntry(entryId: string): Promise<WaitlistEntry> {
    return this.request<WaitlistEntry>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/complete`,
      { method: "POST" },
    );
  }

  async listTables(): Promise<Table[]> {
    return this.request<Table[]>("/tables");
  }

  async listCompatibleTables(entryId: string): Promise<Table[]> {
    return this.request<Table[]>(
      `/waitlist-entries/${encodeURIComponent(entryId)}/compatible-tables`,
    );
  }

  async createTable(input: CreateTableRequest): Promise<Table> {
    return this.request<Table>("/tables", { method: "POST", body: JSON.stringify(input) });
  }

  async updateTable(tableId: string, input: UpdateTableRequest): Promise<Table> {
    return this.request<Table>(`/tables/${encodeURIComponent(tableId)}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  }

  async deleteTable(tableId: string): Promise<void> {
    await this.request<void>(`/tables/${encodeURIComponent(tableId)}`, { method: "DELETE" });
  }

  async setTableAvailability(
    tableId: string,
    input: SetTableAvailabilityRequest,
  ): Promise<Table> {
    return this.request<Table>(`/tables/${encodeURIComponent(tableId)}/availability`, {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  }

  async createLargePartyEnquiry(input: LargePartyEnquiryRequest): Promise<LargePartyEnquiry> {
    return this.request<LargePartyEnquiry>("/large-party-enquiries", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  async listNotifications(): Promise<Notification[]> {
    return this.request<Notification[]>("/notifications");
  }

  async createNotificationEvent(input: {
    entryId: string | null;
    recipientType: NotificationRecipientType;
    channel: NotificationChannel;
    templateType: NotificationTemplateType;
    renderedMessage: string;
  }): Promise<Notification> {
    return this.request<Notification>("/notifications", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }
}
