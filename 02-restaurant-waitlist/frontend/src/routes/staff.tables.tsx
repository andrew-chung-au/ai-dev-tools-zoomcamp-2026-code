import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { waitlistService, type Table, type TableAvailabilityState } from "@/services";

export const Route = createFileRoute("/staff/tables")({
  head: () => ({
    meta: [
      { title: "Table management — Demo Restaurant staff" },
      {
        name: "description",
        content:
          "Create, edit, activate, deactivate and remove tables, and manage availability for the Demo Restaurant walk-in waitlist.",
      },
      { property: "og:title", content: "Table management — Demo Restaurant staff" },
      { property: "og:description", content: "Manage table inventory and availability." },
    ],
  }),
  component: TablesPage,
});

const AVAILABILITY_LABELS: Record<TableAvailabilityState, string> = {
  available: "Available",
  occupied: "Occupied",
  needs_tidying: "Needs tidying",
};

const AVAILABILITY_CLASSES: Record<TableAvailabilityState, string> = {
  available: "border-success bg-success-surface",
  occupied: "border-warning bg-warning-surface",
  needs_tidying: "border-destructive bg-destructive/10",
};

type FormState = {
  name: string;
  minCapacity: string;
  maxCapacity: string;
  notes: string;
};

const emptyForm: FormState = { name: "", minCapacity: "2", maxCapacity: "4", notes: "" };

function TablesPage() {
  const queryClient = useQueryClient();
  const tablesQuery = useQuery({ queryKey: ["tables"], queryFn: () => waitlistService.listTables() });
  const [editingTable, setEditingTable] = useState<Table | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Table | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["tables"] });
  }

  async function run(tableId: string, fn: () => Promise<unknown>) {
    setBusyId(tableId);
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

  const tables = tablesQuery.data ?? [];

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Tables</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Seating and completion update availability automatically. Only active,{" "}
            <strong>available</strong> tables can be selected when seating a new party.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
        >
          New table
        </button>
      </div>

      {actionError && (
        <p
          role="alert"
          className="mt-4 rounded-md border border-destructive p-3 text-sm font-medium text-destructive"
        >
          Error: {actionError}
        </p>
      )}

      {tablesQuery.isLoading && (
        <p role="status" className="mt-6">
          Loading tables…
        </p>
      )}
      {tablesQuery.isError && (
        <p role="alert" className="mt-6 font-medium text-destructive">
          Error: tables could not be loaded.
        </p>
      )}

      {tablesQuery.data && (
        <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {tables.map((table) => {
            const busy = busyId === table.id;
            return (
              <li key={table.id} className={`surface-card p-4 ${!table.active ? "opacity-60" : ""}`}>
                <div className="flex items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold">Table {table.name}</h2>
                  <span
                    className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${AVAILABILITY_CLASSES[table.availabilityState]}`}
                  >
                    {AVAILABILITY_LABELS[table.availabilityState]}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Seats {table.minCapacity}-{table.maxCapacity}
                </p>
                <p className="mt-1 text-sm">
                  {table.active ? "Active" : "Inactive"}
                  {!table.active && " — excluded from seating"}
                </p>
                {table.availabilityState === "occupied" && table.occupyingTicketCode && (
                  <p className="mt-1 text-sm">
                    Occupied by ticket <span className="ticket-code">{table.occupyingTicketCode}</span>
                  </p>
                )}
                {table.notes && (
                  <p className="mt-2 rounded-md border border-border bg-muted p-2 text-sm">
                    {table.notes}
                  </p>
                )}

                <div className="mt-3 flex flex-wrap gap-2">
                  <ActionButton disabled={busy} onClick={() => setEditingTable(table)}>
                    Edit
                  </ActionButton>
                  <ActionButton
                    disabled={busy}
                    onClick={() =>
                      run(table.id, () => waitlistService.updateTable(table.id, { active: !table.active }))
                    }
                  >
                    {table.active ? "Deactivate" : "Activate"}
                  </ActionButton>
                  {table.availabilityState === "needs_tidying" && (
                    <ActionButton
                      disabled={busy}
                      onClick={() =>
                        run(table.id, () =>
                          waitlistService.setTableAvailability(table.id, { availabilityState: "available" }),
                        )
                      }
                    >
                      Mark available
                    </ActionButton>
                  )}
                  {(table.availabilityState === "available" || table.availabilityState === "occupied") && (
                    <ActionButton
                      disabled={busy}
                      onClick={() =>
                        run(table.id, () =>
                          waitlistService.setTableAvailability(table.id, {
                            availabilityState: "needs_tidying",
                          }),
                        )
                      }
                    >
                      Mark needs tidying
                    </ActionButton>
                  )}
                  <ActionButton disabled={busy} tone="destructive" onClick={() => setDeleteTarget(table)}>
                    Delete
                  </ActionButton>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {(creating || editingTable) && (
        <TableFormDialog
          table={editingTable}
          onClose={() => {
            setCreating(false);
            setEditingTable(null);
          }}
          onSubmit={async (values) => {
            if (editingTable) {
              await run(editingTable.id, () =>
                waitlistService.updateTable(editingTable.id, {
                  name: values.name,
                  minCapacity: values.minCapacity,
                  maxCapacity: values.maxCapacity,
                  notes: values.notes ?? null,
                }),
              );
            } else {
              await run("new", () => waitlistService.createTable(values));
            }
            setCreating(false);
            setEditingTable(null);
          }}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          title={`Delete Table ${deleteTarget.name}?`}
          body="This removes the table from the inventory. It cannot be undone. An occupied table cannot be deleted."
          onCancel={() => setDeleteTarget(null)}
          onConfirm={async () => {
            const target = deleteTarget;
            setDeleteTarget(null);
            await run(target.id, () => waitlistService.deleteTable(target.id));
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
        <button
          type="button"
          onClick={onCancel}
          className="h-10 flex-1 rounded-md border border-input px-4 font-medium"
        >
          Keep as is
        </button>
      </div>
    </Overlay>
  );
}

function TableFormDialog({
  table,
  onClose,
  onSubmit,
}: {
  table: Table | null;
  onClose: () => void;
  onSubmit: (values: {
    name: string;
    minCapacity: number;
    maxCapacity: number;
    notes?: string | undefined;
  }) => void;
}) {
  const [form, setForm] = useState<FormState>(
    table
      ? {
          name: table.name,
          minCapacity: String(table.minCapacity),
          maxCapacity: String(table.maxCapacity),
          notes: table.notes ?? "",
        }
      : emptyForm,
  );
  const [error, setError] = useState<string | null>(null);
  const inputClass = "mt-1 h-10 w-full rounded-md border border-input bg-card px-3 text-sm";

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.name.trim()) {
      setError("Table name is required.");
      return;
    }
    const minCapacity = Number(form.minCapacity);
    const maxCapacity = Number(form.maxCapacity);
    if (!Number.isInteger(minCapacity) || minCapacity < 1) {
      setError("Minimum capacity must be a whole number of one or more.");
      return;
    }
    if (!Number.isInteger(maxCapacity) || maxCapacity < minCapacity) {
      setError("Maximum capacity must be a whole number at least as large as the minimum.");
      return;
    }
    setError(null);
    onSubmit({
      name: form.name.trim(),
      minCapacity,
      maxCapacity,
      notes: form.notes.trim() ? form.notes.trim() : undefined,
    });
  }

  return (
    <Overlay label={table ? `Edit Table ${table.name}` : "New table"}>
      <h2 className="text-lg font-semibold">{table ? `Edit Table ${table.name}` : "New table"}</h2>
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label htmlFor="table-name" className="block text-sm font-medium">
            Name
          </label>
          <input
            id="table-name"
            className={inputClass}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="min-capacity" className="block text-sm font-medium">
              Minimum capacity
            </label>
            <input
              id="min-capacity"
              type="number"
              min={1}
              className={inputClass}
              value={form.minCapacity}
              onChange={(e) => setForm((f) => ({ ...f, minCapacity: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="max-capacity" className="block text-sm font-medium">
              Maximum capacity
            </label>
            <input
              id="max-capacity"
              type="number"
              min={1}
              className={inputClass}
              value={form.maxCapacity}
              onChange={(e) => setForm((f) => ({ ...f, maxCapacity: e.target.value }))}
            />
          </div>
        </div>
        <div>
          <label htmlFor="table-notes" className="block text-sm font-medium">
            Notes (optional)
          </label>
          <textarea
            id="table-notes"
            rows={2}
            className="mt-1 w-full rounded-md border border-input bg-card p-3 text-sm"
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          />
        </div>

        {error && <p className="text-sm font-medium text-destructive">Error: {error}</p>}

        <div className="flex gap-2">
          <button
            type="submit"
            className="h-10 flex-1 rounded-md bg-primary px-4 font-medium text-primary-foreground"
          >
            {table ? "Save changes" : "Create table"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="h-10 flex-1 rounded-md border border-input px-4 font-medium"
          >
            Cancel
          </button>
        </div>
      </form>
    </Overlay>
  );
}
