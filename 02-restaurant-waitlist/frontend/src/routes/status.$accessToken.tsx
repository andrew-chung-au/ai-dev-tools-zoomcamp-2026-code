import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { waitlistService, STATUS_LABELS } from "@/services";
import { LogoPlaceholder } from "@/components/LogoPlaceholder";
import { StatusBadge, AttentionBadge } from "@/components/StatusBadge";
import { formatTime } from "@/lib/format";

export const Route = createFileRoute("/status/$accessToken")({
  head: () => ({
    meta: [
      { title: "Your waitlist ticket — Demo Restaurant" },
      {
        name: "description",
        content: "Track your Demo Restaurant walk-in ticket, estimated wait and table-ready status.",
      },
      { property: "og:title", content: "Your waitlist ticket — Demo Restaurant" },
      {
        property: "og:description",
        content: "Track your walk-in ticket, estimated wait and table-ready status.",
      },
    ],
  }),
  component: StatusPage,
});

function StatusPage() {
  const { accessToken } = Route.useParams();
  const queryClient = useQueryClient();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const statusQuery = useQuery({
    queryKey: ["guest-status", accessToken],
    queryFn: () => waitlistService.getGuestEntry(accessToken),
    refetchInterval: 15_000,
  });

  async function confirmCancel() {
    setCancelling(true);
    setActionError(null);
    try {
      await waitlistService.cancelGuestEntry(accessToken);
      await queryClient.invalidateQueries({ queryKey: ["guest-status", accessToken] });
      setConfirmOpen(false);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Cancellation failed.");
    } finally {
      setCancelling(false);
    }
  }

  if (statusQuery.isLoading) {
    return (
      <main className="mx-auto max-w-md px-5 py-10">
        <p role="status">Loading your ticket…</p>
      </main>
    );
  }

  if (statusQuery.isError || !statusQuery.data) {
    return (
      <main className="mx-auto max-w-md px-5 py-10">
        <p role="alert" className="font-medium text-destructive">
          Error: we couldn't find this waitlist entry. Please check the link or ask our host stand.
        </p>
      </main>
    );
  }

  const status = statusQuery.data;

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <header className="flex items-center gap-3">
        <LogoPlaceholder label={status.venueLogoPlaceholderLabel} />
        <h1 className="text-xl font-semibold">{status.venueName}</h1>
      </header>

      {status.status === "notified" && (
        <section
          className={`mt-6 rounded-lg border-2 p-5 ${
            status.needsAttention ? "border-destructive bg-warning-surface" : "border-success bg-success-surface"
          }`}
        >
          <h2 className="text-lg font-semibold">Your table is ready</h2>
          <p className="ticket-code mt-2 text-5xl">{status.ticketCode}</p>
          <p className="mt-3">{status.message}</p>
          <p className="mt-3 text-sm">
            Notified at <strong>{formatTime(status.notifiedAt)}</strong> · please return by{" "}
            <strong>{formatTime(status.returnByAt)}</strong>.
          </p>
          {status.needsAttention && (
            <p className="mt-3">
              <AttentionBadge>Return time passed — needs attention</AttentionBadge>
              <span className="mt-2 block text-sm">
                Your return time has passed. Please speak to our host stand as soon as you can.
              </span>
            </p>
          )}
        </section>
      )}

      <section className="surface-card mt-6 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm text-muted-foreground">Ticket</p>
            <p className="ticket-code text-3xl">{status.ticketCode}</p>
          </div>
          <StatusBadge status={status.status} />
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-muted-foreground">Name</dt>
            <dd className="font-medium">{status.guestName}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Party size</dt>
            <dd className="font-medium">{status.partySize}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Status</dt>
            <dd className="font-medium">{STATUS_LABELS[status.status]}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Estimated wait</dt>
            <dd className="font-medium">{status.estimatedWaitMinutes} minutes</dd>
          </div>
        </dl>
        <p className="mt-4">{status.message}</p>
        <p className="mt-2 text-xs text-muted-foreground">
          Wait times are estimates only and are not a guaranteed seating time.
        </p>
      </section>

      {status.cancellationAllowed && (
        <section className="mt-6">
          {!confirmOpen ? (
            <button
              type="button"
              onClick={() => setConfirmOpen(true)}
              className="h-11 w-full rounded-md border border-destructive px-4 font-medium text-destructive"
            >
              Cancel my waitlist entry
            </button>
          ) : (
            <div role="dialog" aria-label="Confirm cancellation" className="surface-card p-4">
              <p className="font-medium">Cancel ticket {status.ticketCode}?</p>
              <p className="mt-1 text-sm text-muted-foreground">
                This removes your party from tonight's waitlist. You can join again afterwards.
              </p>
              {actionError && (
                <p role="alert" className="mt-2 text-sm font-medium text-destructive">
                  Error: {actionError}
                </p>
              )}
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  onClick={confirmCancel}
                  disabled={cancelling}
                  className="h-11 flex-1 rounded-md bg-destructive px-4 font-medium text-destructive-foreground disabled:opacity-60"
                >
                  {cancelling ? "Cancelling…" : "Yes, cancel"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmOpen(false)}
                  className="h-11 flex-1 rounded-md border border-input px-4 font-medium"
                >
                  Keep my place
                </button>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
