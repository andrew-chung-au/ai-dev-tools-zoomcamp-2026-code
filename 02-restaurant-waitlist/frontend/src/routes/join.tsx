import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { waitlistService, type CreateGuestEntryResult } from "@/services";
import { LogoPlaceholder } from "@/components/LogoPlaceholder";

export const Route = createFileRoute("/join")({
  head: () => ({
    meta: [
      { title: "Join the waitlist — Demo Restaurant" },
      {
        name: "description",
        content:
          "Join the Demo Restaurant walk-in waitlist, get a ticket code, and track your estimated wait from your phone.",
      },
      { property: "og:title", content: "Join the waitlist — Demo Restaurant" },
      {
        property: "og:description",
        content: "Get a walk-in ticket and track your estimated wait from your phone.",
      },
    ],
  }),
  component: JoinPage,
});

interface FieldErrors {
  guestName?: string;
  partySize?: string;
  mobileNumber?: string;
  policy?: string;
  form?: string;
}

function JoinPage() {
  const venueQuery = useQuery({ queryKey: ["venue"], queryFn: () => waitlistService.getVenue() });
  const [guestName, setGuestName] = useState("");
  const [partySize, setPartySize] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [seatingNote, setSeatingNote] = useState("");
  const [policyAcknowledged, setPolicyAcknowledged] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<CreateGuestEntryResult | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const venue = venueQuery.data;

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const nextErrors: FieldErrors = {};
    if (!guestName.trim()) nextErrors.guestName = "Enter the name for your party.";
    const size = Number(partySize);
    if (!partySize.trim()) nextErrors.partySize = "Enter how many people are in your party.";
    else if (!Number.isInteger(size) || size < 1)
      nextErrors.partySize = "Party size must be a whole number of one or more.";
    if (!mobileNumber.trim()) nextErrors.mobileNumber = "Enter a mobile number.";
    else if (!/^\+?[0-9][0-9\s-]{6,17}$/.test(mobileNumber.trim()))
      nextErrors.mobileNumber = "Enter a valid mobile number, for example +61 400 000 000.";
    if (!policyAcknowledged) nextErrors.policy = "You must acknowledge the waitlist policy.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const response = await waitlistService.createGuestEntry({
        guestName,
        partySize: size,
        mobileNumber,
        seatingNote,
        policyAcknowledged,
      });
      setResult(response);
      if (response.kind === "entry") setAccessToken(response.accessToken);
    } catch (error) {
      setErrors({ form: error instanceof Error ? error.message : "Something went wrong." });
    } finally {
      setSubmitting(false);
    }
  }

  if (venueQuery.isLoading) {
    return (
      <main className="mx-auto max-w-md px-5 py-10">
        <p role="status">Loading the waitlist…</p>
      </main>
    );
  }

  if (venueQuery.isError || !venue) {
    return (
      <main className="mx-auto max-w-md px-5 py-10">
        <p role="alert" className="font-medium text-destructive">
          Error: we couldn't load the waitlist. Please refresh and try again.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-md px-5 py-8">
      <header className="flex items-center gap-3">
        <LogoPlaceholder label={venue.logoPlaceholderLabel} />
        <div>
          <h1 className="text-xl font-semibold">{venue.name}</h1>
          <p className="text-sm">
            Waitlist status:{" "}
            <span className="font-semibold">{venue.waitlistOpen ? "Open" : "Closed"}</span>
          </p>
        </div>
      </header>

      {result ? (
        <section className="surface-card mt-6 p-5" aria-live="polite">
          {result.kind === "entry" && (
            <>
              <h2 className="text-lg font-semibold">You're on the waitlist</h2>
              <p className="ticket-code mt-3 text-4xl">{result.entry.ticketCode}</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Party of {result.entry.partySize} · estimated wait about{" "}
                {result.entry.estimatedWaitMinutes} minutes (not a guaranteed seating time).
              </p>
              <p className="mt-3">{result.message}</p>
              {accessToken && (
                <Link
                  to="/status/$accessToken"
                  params={{ accessToken }}
                  className="mt-5 inline-flex h-11 items-center rounded-md bg-primary px-4 font-medium text-primary-foreground"
                >
                  View my status page
                </Link>
              )}
            </>
          )}
          {result.kind === "large_party_enquiry" && (
            <>
              <h2 className="text-lg font-semibold">Large-party request sent</h2>
              <p className="mt-2">{venue.messages.largePartyMessage}</p>
              <p className="mt-3">{result.message}</p>
              <p className="mt-3 text-sm">
                Your enquiry reference is{" "}
                <span className="ticket-code">{result.enquiry.reference}</span>. This is not a
                confirmed booking or waitlist ticket.
              </p>
              <p className="mt-3 text-sm">
                Next step: call us on <span className="font-semibold">{venue.contactPhone}</span> if
                you'd like to talk sooner.
              </p>
            </>
          )}
          {result.kind === "closed" && (
            <>
              <h2 className="text-lg font-semibold">Waitlist closed</h2>
              <p className="mt-2">{result.message}</p>
            </>
          )}
        </section>
      ) : !venue.waitlistOpen ? (
        <section className="surface-card mt-6 p-5">
          <h2 className="text-lg font-semibold">Waitlist closed</h2>
          <p className="mt-2">{venue.messages.closedWaitlistMessage}</p>
          <p className="mt-3 text-sm text-muted-foreground">
            The join form is unavailable while the waitlist is closed.
          </p>
        </section>
      ) : (
        <>
          <p className="mt-4">{venue.messages.joinMessage}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Online parties of up to {venue.maxOnlinePartySize} guests. Larger groups can send us an
            enquiry instead.
          </p>

          <form onSubmit={onSubmit} noValidate className="mt-6 space-y-5">
            <div>
              <label htmlFor="guestName" className="block text-sm font-medium">
                Name for the party
              </label>
              <input
                id="guestName"
                name="guestName"
                type="text"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
                aria-invalid={Boolean(errors.guestName)}
                aria-describedby={errors.guestName ? "guestName-error" : undefined}
                className="mt-1 h-11 w-full rounded-md border border-input bg-card px-3 text-base"
              />
              {errors.guestName && (
                <p id="guestName-error" className="mt-1 text-sm font-medium text-destructive">
                  Error: {errors.guestName}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="partySize" className="block text-sm font-medium">
                Party size
              </label>
              <input
                id="partySize"
                name="partySize"
                type="number"
                min={1}
                inputMode="numeric"
                value={partySize}
                onChange={(e) => setPartySize(e.target.value)}
                aria-invalid={Boolean(errors.partySize)}
                aria-describedby={errors.partySize ? "partySize-error" : undefined}
                className="mt-1 h-11 w-full rounded-md border border-input bg-card px-3 text-base"
              />
              {errors.partySize && (
                <p id="partySize-error" className="mt-1 text-sm font-medium text-destructive">
                  Error: {errors.partySize}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="mobileNumber" className="block text-sm font-medium">
                Mobile number
              </label>
              <input
                id="mobileNumber"
                name="mobileNumber"
                type="tel"
                value={mobileNumber}
                onChange={(e) => setMobileNumber(e.target.value)}
                aria-invalid={Boolean(errors.mobileNumber)}
                aria-describedby={errors.mobileNumber ? "mobileNumber-error" : undefined}
                className="mt-1 h-11 w-full rounded-md border border-input bg-card px-3 text-base"
              />
              {errors.mobileNumber && (
                <p id="mobileNumber-error" className="mt-1 text-sm font-medium text-destructive">
                  Error: {errors.mobileNumber}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="seatingNote" className="block text-sm font-medium">
                Seating or accessibility note (optional)
              </label>
              <textarea
                id="seatingNote"
                name="seatingNote"
                rows={3}
                value={seatingNote}
                onChange={(e) => setSeatingNote(e.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-card p-3 text-base"
              />
            </div>

            <fieldset className="rounded-md border border-border p-3">
              <legend className="px-1 text-sm font-medium">Waitlist policy</legend>
              <p className="text-sm">{venue.messages.policyAcknowledgementMessage}</p>
              <div className="mt-3 flex items-start gap-3">
                <input
                  id="policy"
                  name="policy"
                  type="checkbox"
                  checked={policyAcknowledged}
                  onChange={(e) => setPolicyAcknowledged(e.target.checked)}
                  aria-invalid={Boolean(errors.policy)}
                  aria-describedby={errors.policy ? "policy-error" : undefined}
                  className="mt-1 h-5 w-5"
                />
                <label htmlFor="policy" className="text-sm font-medium">
                  I have read and accept the waitlist policy
                </label>
              </div>
              {errors.policy && (
                <p id="policy-error" className="mt-2 text-sm font-medium text-destructive">
                  Error: {errors.policy}
                </p>
              )}
            </fieldset>

            {errors.form && (
              <p role="alert" className="text-sm font-medium text-destructive">
                Error: {errors.form}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="h-12 w-full rounded-md bg-primary px-4 text-base font-medium text-primary-foreground disabled:opacity-60"
            >
              {submitting ? "Joining…" : "Join waitlist"}
            </button>
          </form>
        </>
      )}
    </main>
  );
}
