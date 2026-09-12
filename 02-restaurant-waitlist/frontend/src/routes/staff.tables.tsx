import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { waitlistService } from "@/services";

export const Route = createFileRoute("/staff/tables")({
  head: () => ({
    meta: [
      { title: "Table inventory — Demo Restaurant staff" },
      {
        name: "description",
        content: "Live table capacity and occupancy for the Demo Restaurant walk-in waitlist.",
      },
      { property: "og:title", content: "Table inventory — Demo Restaurant staff" },
      { property: "og:description", content: "Live table capacity and occupancy." },
    ],
  }),
  component: TablesPage,
});

function TablesPage() {
  const tablesQuery = useQuery({ queryKey: ["tables"], queryFn: () => waitlistService.listTables() });

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <h1 className="text-2xl font-semibold">Tables</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Seating is assigned from the waitlist. A table becomes available again when its party is
        completed.
      </p>

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
          {tablesQuery.data.map((table) => (
            <li key={table.id} className="surface-card p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Table {table.name}</h2>
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                    table.occupied
                      ? "border-warning bg-warning-surface"
                      : "border-success bg-success-surface"
                  }`}
                >
                  {table.occupied ? "Occupied" : "Available"}
                </span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">Seats {table.capacity}</p>
              <p className="mt-1 text-sm">
                {table.occupied ? (
                  <>
                    Occupied by ticket <span className="ticket-code">{table.occupyingTicketCode}</span>
                  </>
                ) : (
                  "No party assigned"
                )}
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
