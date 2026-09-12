import { STATUS_LABELS, type WaitlistStatus } from "@/services";

const STATUS_STYLES: Record<WaitlistStatus, string> = {
  pending: "bg-info-surface text-foreground border-border",
  waiting: "bg-secondary text-secondary-foreground border-border",
  notified: "bg-warning-surface text-foreground border-warning",
  seated: "bg-success-surface text-foreground border-success",
  completed: "bg-muted text-muted-foreground border-border",
  cancelled: "bg-muted text-muted-foreground border-border",
  no_show: "bg-muted text-muted-foreground border-border",
};

export function StatusBadge({ status }: { status: WaitlistStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

export function AttentionBadge({ children }: { children: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-destructive bg-warning-surface px-2.5 py-0.5 text-xs font-semibold text-foreground">
      <span aria-hidden="true">!</span>
      {children}
    </span>
  );
}

export function ReviewBadge() {
  return (
    <span className="inline-flex items-center rounded-full border border-accent bg-warning-surface px-2.5 py-0.5 text-xs font-semibold text-foreground">
      Review required
    </span>
  );
}
