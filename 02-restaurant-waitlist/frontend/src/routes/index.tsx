import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Demo Restaurant Waitlist Manager" },
      {
        name: "description",
        content:
          "Walk-in waitlist prototype for an independent restaurant: guest join page, guest status, and staff queue management.",
      },
      { property: "og:title", content: "Demo Restaurant Waitlist Manager" },
      {
        property: "og:description",
        content: "Guest join, live ticket status, and a staff queue dashboard for walk-in dining.",
      },
    ],
  }),
  component: Home,
});

function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-5 py-12">
      <div>
        <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Frontend prototype
        </p>
        <h1 className="mt-2 text-3xl font-semibold">Demo Restaurant waitlist manager</h1>
        <p className="mt-3 text-muted-foreground">
          A configurable walk-in waitlist for one venue. All data is mocked in the browser; no
          messages are sent.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          to="/join"
          className="surface-card block p-5 transition-colors hover:bg-secondary"
        >
          <h2 className="text-lg font-semibold">Guest join page</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            The mobile page behind the table QR code.
          </p>
        </Link>
        <Link
          to="/login"
          className="surface-card block p-5 transition-colors hover:bg-secondary"
        >
          <h2 className="text-lg font-semibold">Staff sign in</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Queue dashboard, tables and venue settings.
          </p>
        </Link>
      </div>
    </main>
  );
}
