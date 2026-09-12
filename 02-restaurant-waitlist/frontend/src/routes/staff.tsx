import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { waitlistService } from "@/services";
import { LogoPlaceholder } from "@/components/LogoPlaceholder";
import { getSession } from "@/lib/session";

export const Route = createFileRoute("/staff")({
  component: StaffLayout,
});

const navLinkClass =
  "rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-secondary";

function StaffLayout() {
  const { data: venue } = useQuery({
    queryKey: ["venue"],
    queryFn: () => waitlistService.getVenue(),
  });
  const session = getSession();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 py-3">
          <LogoPlaceholder label={venue?.logoPlaceholderLabel ?? "Venue logo placeholder"} size="sm" />
          <div className="mr-auto">
            <p className="font-semibold">{venue?.name ?? "Loading venue…"}</p>
            <p className="text-xs text-muted-foreground">
              Staff console {session ? `— signed in as ${session.staffName} (mocked)` : "— demo session"}
            </p>
          </div>
          <nav aria-label="Staff sections" className="flex flex-wrap gap-1">
            <Link to="/staff" activeOptions={{ exact: true }} activeProps={{ className: "bg-secondary rounded-md px-3 py-2 text-sm font-semibold" }} className={navLinkClass}>
              Waitlist
            </Link>
            <Link to="/staff/tables" activeProps={{ className: "bg-secondary rounded-md px-3 py-2 text-sm font-semibold" }} className={navLinkClass}>
              Tables
            </Link>
            <Link to="/staff/settings" activeProps={{ className: "bg-secondary rounded-md px-3 py-2 text-sm font-semibold" }} className={navLinkClass}>
              Settings
            </Link>
            <Link to="/login" className={navLinkClass}>
              Sign out
            </Link>
          </nav>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
