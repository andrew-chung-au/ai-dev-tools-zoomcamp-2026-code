import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  waitlistService,
  isNeedsAttention,
  PARTY_CLASS_LABELS,
  STATUS_LABELS,
  type PartySizeClass,
  type Table,
  type WaitlistEntry,
  type WaitlistFilters,
  type WaitlistStatus,
} from "@/services";
import { StatusBadge, AttentionBadge, ReviewBadge } from "@/components/StatusBadge";
import { formatDate, formatTime } from "@/lib/format";

export const Route = createFileRoute("/staff/")({
  head: () => ({
    meta: [
      { title: "Waitlist dashboard — Demo Restaurant staff" },
      {
        name: "description",
        content:
          "Manage tonight's walk-in queue: approve, notify, seat and complete parties at Demo Restaurant.",
      },
      { property: "og:title", content: "Waitlist dashboard — Demo Restaurant staff" },
      {
        property: "og:description",
        content: "Approve, notify, seat and complete walk-in parties.",
      },
    ],
  }),
  component: StaffDashboard,
});

const STATUS_OPTIONS: (WaitlistStatus | "all")[] = [
  "all",
  "pending",
  "waiting",
  "notified",
  "seated",
  "completed",
  "cancelled",
  "no_show",
];

type Confirm = { entry: WaitlistEntry; action: "cancel" | "no_show" } | null;

function StaffDashboard() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<WaitlistFilters>({
    status: "all",
    partySizeClass: "all",
    reviewRequiredOnly: false,
    needsAttentionOnly: false,
  });
  const [detailsEntry, setDetailsEntry] = useState<WaitlistEntry | null>(null);
  const [seatEntry, setSeatEntry] = useState<WaitlistEntry | null>(null);
  const [confirm, setConfirm] = useState<Confirm>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => waitlistService.getDashboard(),
    refetchInterval: 20_000,
  });

  const entriesQuery = useQuery({
    queryKey: ["entries", filters],
    queryFn: () => waitlistService.listWaitlistEntries(filters),
  });

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["entries"] }),
      queryClient.invalidateQueries({ queryKey: ["tables"] }),
    ]);
  }

  async function run(entryId: string, fn: () => Promise<unknown>) {
    setBusyId(entryId);
    setActionError(null);
    try {
      await fn();
      await refresh();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Action failed.");
    } finally {
      setBusyId(null);
    }
  }

  const summary = dashboardQuery.data?.summary;
  const venue = dashboardQuery.data?.venue;
  const entries = entriesQuery.data ?? [];

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Tonight's waitlist</h1>
          <p className="text-sm text-muted-foreground">
            Service date:{" "}
            {dashboardQuery.data ? formatDate(dashboardQuery.data.serviceDate) : "loading…"}
            {venue && ` · waitlist ${venue.waitlistOpen ? "open" : "closed"}`}
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="h-10 rounded-md border border-input px-4 text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      <section aria-label="Queue summary" className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Active waiting", value: summary?.activeWaiting },
          { label: "Pending review", value: summary?.pendingReview },
          { label: "Notified", value: summary?.notified },
          { label: "Needs attention", value: summary?.needsAttention },
        ].map((card) => (
          <div key={card.label} className="surface-card p-4">
            <p className="text-sm text-muted-foreground">{card.label}</p>
            <p className="mt-1 text-3xl font-semibold">{card.value ?? "—"}</p>
          </div>
        ))}
      </section>

      <section aria-label="Filters" className="surface-card mt-5 flex flex-wrap items-end gap-4 p-4">
        <div>
          <label htmlFor="filter-status" className="block text-sm font-medium">
            Status
          </label>
          <select
            id="filter-status"
            value={filters.status}
            onChange={(e) =>
              setFilters((f) => ({ ...f, status: e.target.value as WaitlistStatus | "all" }))
            }
            className="mt-1 h-10 rounded-md border border-input bg-card px-2 text-sm"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option === "all" ? "All statuses" : STATUS_LABELS[option]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filter-class" className="block text-sm font-medium">
            Party-size class
          </label>
          <select
            id="filter-class"
            value={filters.partySizeClass}
            onChange={(e) =>
              setFilters((f) => ({ ...f, partySizeClass: e.target.value as PartySizeClass | "all" }))
            }
            className="mt-1 h-10 rounded-md border border-input bg-card px-2 text-sm"
          >
            <option value="all">All classes</option>
            {(["A", "B", "C", "D"] as PartySizeClass[]).map((cls) => (
              <option key={cls} value={cls}>
                {PARTY_CLASS_LABELS[cls]}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <input
            id="filter-review"
            type="checkbox"
            checked={Boolean(filters.reviewRequiredOnly)}
            onChange={(e) => setFilters((f) => ({ ...f, reviewRequiredOnly: e.target.checked }))}
            className="h-5 w-5"
          />
          <label htmlFor="filter-review" className="text-sm font-medium">
            Review required only
          </label>
        </div>
        <div className="flex items-center gap-2">
          <input
            id="filter-attention"
            type="checkbox"
            checked={Boolean(filters.needsAttentionOnly)}
            onChange={(e) => setFilters((f) => ({ ...f, needsAttentionOnly: e.target.checked }))}
            className="h-5 w-5"
          />
          <label htmlFor="filter-attention" className="text-sm font-medium">
            Needs attention only
          </label>
        </div>
      </section>

      {actionError && (
        <p role="alert" className="mt-4 rounded-md border border-destructive p-3 text-sm font-medium text-destructive">
          Error: {actionError}
        </p>
      )}

      <section aria-label="Waitlist entries" className="mt-5 space-y-3">
        {entriesQuery.isLoading && <p role="status">Loading waitlist entries…</p>}
        {entriesQuery.isError && (
          <p role="alert" className="font-medium text-destructive">
            Error: the waitlist could not be loaded. Try refreshing.
          </p>
        )}
        {entriesQuery.data && entries.length === 0 && (
          <div className="surface-card p-6 text-center">
            <p className="font-medium">No entries match these filters</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Clear a filter, or wait for the next guest to join from the QR page.
            </p>
          </div>
        )}

        {entries.map((entry) => {
          const overdue = isNeedsAttention(entry);
          const busy = busyId === entry.id;
          return (
            <article
              key={entry.id}
              className={`surface-card p-4 ${overdue ? "border-l-4 border-l-destructive" : ""}`}
            >
              <div className="flex flex-wrap items-start gap-x-6 gap-y-2">
                <div className="min-w-32">
                  <p className="ticket-code text-2xl">{entry.ticketCode}</p>
                  <p className="text-sm text-muted-foreground">
                    Arrived {formatTime(entry.arrivalTime)}
                  </p>
                </div>
                <div className="min-w-48 grow">
                  <p className="font-semibold">{entry.guestName}</p>
                  <p className="text-sm text-muted-foreground">
                    Party of {entry.partySize} · original class {entry.originalPartyClass} · seating
                    class {entry.currentSeatingClass} · est. {entry.estimatedWaitMinutes} min
                  </p>
                  {entry.tableName && (
                    <p className="text-sm">Table {entry.tableName}</p>
                  )}
                  {entry.status === "notified" && (
                    <p className="text-sm">
                      Notified {formatTime(entry.notifiedAt)} · return by{" "}
                      <strong>{formatTime(entry.returnByAt)}</strong>
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge status={entry.status} />
                  {entry.reviewRequired && <ReviewBadge />}
                  {overdue && <AttentionBadge>Needs attention</AttentionBadge>}
                </div>
              </div>

              {entry.reviewRequired && entry.reviewReason && (
                <p className="mt-2 rounded-md border border-accent bg-warning-surface p-2 text-sm">
                  {entry.reviewReason} The ticket code stays the same.
                </p>
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                {entry.status === "pending" && (
                  <ActionButton disabled={busy} onClick={() => run(entry.id, () => waitlistService.approveEntry(entry.id))}>
                    Approve
                  </ActionButton>
                )}
                {entry.status === "waiting" && (
                  <ActionButton disabled={busy} onClick={() => run(entry.id, () => waitlistService.notifyEntry(entry.id))}>
                    Notify guest
                  </ActionButton>
                )}
                {(entry.status === "waiting" || entry.status === "notified" || entry.status === "pending") && (
                  <ActionButton disabled={busy} onClick={() => setSeatEntry(entry)}>
                    Seat…
                  </ActionButton>
                )}
                {entry.status === "notified" && (
                  <>
                    <ActionButton disabled={busy} onClick={() => run(entry.id, () => waitlistService.extendReturnBy(entry.id, 5))}>
                      Extend 5 min
                    </ActionButton>
                    <ActionButton disabled={busy} onClick={() => run(entry.id, () => waitlistService.returnToWaiting(entry.id))}>
                      Return to waiting
                    </ActionButton>
                    <ActionButton disabled={busy} tone="destructive" onClick={() => setConfirm({ entry, action: "no_show" })}>
                      Mark no-show
                    </ActionButton>
                  </>
                )}
                {entry.status === "seated" && (
                  <ActionButton disabled={busy} onClick={() => run(entry.id, () => waitlistService.completeEntry(entry.id))}>
                    Complete party
                  </ActionButton>
                )}
                {!["completed", "cancelled", "no_show"].includes(entry.status) && (
                  <ActionButton disabled={busy} tone="destructive" onClick={() => setConfirm({ entry, action: "cancel" })}>
                    Cancel entry
                  </ActionButton>
                )}
                <ActionButton disabled={busy} onClick={() => setDetailsEntry(entry)}>
                  Details
                </ActionButton>
              </div>
            </article>
          );
        })}
      </section>

      {detailsEntry && (
        <DetailsPanel
          entry={detailsEntry}
          onClose={() => setDetailsEntry(null)}
          onUpdateEstimate={(minutes) =>
            run(detailsEntry.id, () => waitlistService.updateWaitEstimate(detailsEntry.id, minutes))
          }
        />
      )}

      {seatEntry && (
        <SeatDialog
          entry={seatEntry}
          onClose={() => setSeatEntry(null)}
          onSeat={async (tableId, reason) => {
            await run(seatEntry.id, () =>
              waitlistService.seatEntry(seatEntry.id, {
                tableId,
                seatingOverrideReason: reason,
              }),
            );
            setSeatEntry(null);
          }}
        />
      )}

      {confirm && (
        <ConfirmDialog
          title={
            confirm.action === "cancel"
              ? `Cancel ${confirm.entry.ticketCode}?`
              : `Mark ${confirm.entry.ticketCode} as a no-show?`
          }
          body={
            confirm.action === "cancel"
              ? "The party is removed from the active queue. The ticket code stays reserved and is not reused."
              : "Use this when a notified guest did not return before their return-by time."
          }
          onCancel={() => setConfirm(null)}
          onConfirm={async () => {
            const { entry, action } = confirm;
            setConfirm(null);
            await run(entry.id, () =>
              action === "cancel"
                ? waitlistService.cancelEntry(entry.id)
                : waitlistService.markNoShow(entry.id),
            );
          }}
        />
      )}
    </main>
  );
}

function ActionButton({
  children,
  onClick,
  disabled,
  tone = "default",
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  tone?: "default" | "destructive";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`h-9 rounded-md border px-3 text-sm font-medium disabled:opacity-50 ${
        tone === "destructive"
          ? "border-destructive text-destructive"
          : "border-input bg-card hover:bg-secondary"
      }`}
    >
      {children}
    </button>
  );
}

function Overlay({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 p-4">
      <div role="dialog" aria-modal="true" aria-label={label} className="surface-card w-full max-w-md p-5">
        {children}
      </div>
    </div>
  );
}

function ConfirmDialog({
  title,
  body,
  onConfirm,
  onCancel,
}: {
  title: string;
  body: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Overlay label={title}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{body}</p>
      <div className="mt-5 flex gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="h-10 flex-1 rounded-md bg-destructive px-4 font-medium text-destructive-foreground"
        >
          Confirm
        </button>
        <button type="button" onClick={onCancel} className="h-10 flex-1 rounded-md border border-input px-4 font-medium">
          Keep as is
        </button>
      </div>
    </Overlay>
  );
}

function DetailsPanel({
  entry,
  onClose,
  onUpdateEstimate,
}: {
  entry: WaitlistEntry;
  onClose: () => void;
  onUpdateEstimate: (minutes: number) => void;
}) {
  const [estimate, setEstimate] = useState(String(entry.estimatedWaitMinutes));
  const [error, setError] = useState<string | null>(null);

  return (
    <Overlay label={`Details for ${entry.ticketCode}`}>
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-lg font-semibold">
          <span className="ticket-code">{entry.ticketCode}</span> — {entry.guestName}
        </h2>
        <button type="button" onClick={onClose} className="h-9 rounded-md border border-input px-3 text-sm">
          Close
        </button>
      </div>
      <dl className="mt-4 space-y-2 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Contact (staff only)</dt>
          <dd className="font-medium">{entry.mobileNumber}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Seating note</dt>
          <dd className="text-right">{entry.seatingNote ?? "None"}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Original party size</dt>
          <dd>{entry.originalPartySize}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Seating override reason</dt>
          <dd className="text-right">{entry.seatingOverrideReason ?? "None"}</dd>
        </div>
      </dl>

      <div className="mt-5">
        <label htmlFor="estimate" className="block text-sm font-medium">
          Estimated wait (minutes)
        </label>
        <div className="mt-1 flex gap-2">
          <input
            id="estimate"
            type="number"
            min={0}
            value={estimate}
            onChange={(e) => setEstimate(e.target.value)}
            className="h-10 w-32 rounded-md border border-input bg-card px-3"
          />
          <button
            type="button"
            onClick={() => {
              const value = Number(estimate);
              if (!Number.isInteger(value) || value < 0) {
                setError("Enter a whole number of minutes.");
                return;
              }
              setError(null);
              onUpdateEstimate(value);
              onClose();
            }}
            className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
          >
            Save estimate
          </button>
        </div>
        {error && <p className="mt-1 text-sm font-medium text-destructive">Error: {error}</p>}
      </div>
    </Overlay>
  );
}

function SeatDialog({
  entry,
  onClose,
  onSeat,
}: {
  entry: WaitlistEntry;
  onClose: () => void;
  onSeat: (tableId: string, reason?: string) => void;
}) {
  const [tableId, setTableId] = useState("");
  const [reason, setReason] = useState("");
  const tablesQuery = useQuery<Table[]>({
    queryKey: ["compatible-tables", entry.id],
    queryFn: () => waitlistService.listCompatibleTables(entry.id),
  });

  return (
    <Overlay label={`Seat ${entry.ticketCode}`}>
      <h2 className="text-lg font-semibold">
        Seat <span className="ticket-code">{entry.ticketCode}</span> — party of {entry.partySize}
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Only available tables with enough capacity are listed. Seating is not strictly first-in
        first-out: a later compatible party may be seated first.
      </p>

      {tablesQuery.isLoading && <p role="status" className="mt-4 text-sm">Loading tables…</p>}
      {tablesQuery.data && tablesQuery.data.length === 0 && (
        <p className="mt-4 text-sm font-medium">
          No compatible table is free right now. Complete a seated party to release a table.
        </p>
      )}

      {tablesQuery.data && tablesQuery.data.length > 0 && (
        <>
          <fieldset className="mt-4">
            <legend className="text-sm font-medium">Compatible tables</legend>
            <div className="mt-2 space-y-2">
              {tablesQuery.data.map((table) => (
                <div key={table.id} className="flex items-center gap-3">
                  <input
                    id={`table-${table.id}`}
                    type="radio"
                    name="table"
                    value={table.id}
                    checked={tableId === table.id}
                    onChange={() => setTableId(table.id)}
                    className="h-5 w-5"
                  />
                  <label htmlFor={`table-${table.id}`} className="text-sm">
                    Table {table.name} · seats {table.capacity}
                  </label>
                </div>
              ))}
            </div>
          </fieldset>

          <div className="mt-4">
            <label htmlFor="override" className="block text-sm font-medium">
              Seating override reason (optional)
            </label>
            <input
              id="override"
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. only compatible table free"
              className="mt-1 h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
            />
          </div>
        </>
      )}

      <div className="mt-5 flex gap-2">
        <button
          type="button"
          disabled={!tableId}
          onClick={() => onSeat(tableId, reason)}
          className="h-10 flex-1 rounded-md bg-primary px-4 font-medium text-primary-foreground disabled:opacity-50"
        >
          Seat party
        </button>
        <button type="button" onClick={onClose} className="h-10 flex-1 rounded-md border border-input px-4 font-medium">
          Cancel
        </button>
      </div>
    </Overlay>
  );
}
