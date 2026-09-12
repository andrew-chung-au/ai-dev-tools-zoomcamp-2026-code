import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  waitlistService,
  type EntryMode,
  type PartySizeClass,
  type Venue,
  type VenueMessageSettings,
} from "@/services";
import { LogoPlaceholder } from "@/components/LogoPlaceholder";

export const Route = createFileRoute("/staff/settings")({
  head: () => ({
    meta: [
      { title: "Venue settings — Demo Restaurant staff" },
      {
        name: "description",
        content:
          "Configure waitlist limits, grace period, entry mode and guest-facing messages for Demo Restaurant.",
      },
      { property: "og:title", content: "Venue settings — Demo Restaurant staff" },
      { property: "og:description", content: "Configure waitlist limits and guest messages." },
    ],
  }),
  component: SettingsPage,
});

const MESSAGE_FIELDS: { key: keyof VenueMessageSettings; label: string }[] = [
  { key: "joinMessage", label: "Join message" },
  { key: "policyAcknowledgementMessage", label: "Policy acknowledgement message" },
  { key: "confirmationMessage", label: "Confirmation message" },
  { key: "tableReadyMessage", label: "Table-ready message" },
  { key: "cancellationMessage", label: "Cancellation message" },
  { key: "closedWaitlistMessage", label: "Closed waitlist message" },
  { key: "largePartyMessage", label: "Large-party message" },
  { key: "largePartyConfirmationMessage", label: "Large-party confirmation message" },
];

function SettingsPage() {
  const queryClient = useQueryClient();
  const venueQuery = useQuery({ queryKey: ["venue"], queryFn: () => waitlistService.getVenue() });
  const [draft, setDraft] = useState<Venue | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (venueQuery.data && !draft) setDraft(venueQuery.data);
  }, [venueQuery.data, draft]);

  if (venueQuery.isLoading || !draft) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-6">
        <p role="status">Loading venue settings…</p>
      </main>
    );
  }

  if (venueQuery.isError) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-6">
        <p role="alert" className="font-medium text-destructive">
          Error: venue settings could not be loaded.
        </p>
      </main>
    );
  }

  const update = (patch: Partial<Venue>) => {
    setDraft({ ...draft, ...patch });
    setSaved(false);
  };

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setError(null);
    try {
      await waitlistService.updateVenue({
        name: draft.name,
        contactPhone: draft.contactPhone,
        staffNotificationEmail: draft.staffNotificationEmail,
        menuUrl: draft.menuUrl,
        maxOnlinePartySize: draft.maxOnlinePartySize,
        gracePeriodMinutes: draft.gracePeriodMinutes,
        entryMode: draft.entryMode,
        waitlistOpen: draft.waitlistOpen,
        defaultWaitEstimateMinutes: draft.defaultWaitEstimateMinutes,
        messages: draft.messages,
      });
      await queryClient.invalidateQueries({ queryKey: ["venue"] });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Settings could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const inputClass = "mt-1 h-10 w-full rounded-md border border-input bg-card px-3 text-sm";

  return (
    <main className="mx-auto max-w-4xl px-4 py-6">
      <h1 className="text-2xl font-semibold">Venue settings</h1>

      <form onSubmit={onSave} className="mt-6 space-y-6">
        <section className="surface-card p-5">
          <h2 className="text-lg font-semibold">Venue</h2>
          <div className="mt-4 flex items-center gap-4">
            <LogoPlaceholder label={draft.logoPlaceholderLabel} size="lg" />
            <p className="text-sm text-muted-foreground">
              Logo preview area. Real logo upload is deferred to the backend phase; this prototype
              always shows a neutral placeholder.
            </p>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="venue-name" className="block text-sm font-medium">
                Venue name
              </label>
              <input id="venue-name" className={inputClass} value={draft.name} onChange={(e) => update({ name: e.target.value })} />
            </div>
            <div>
              <label htmlFor="phone" className="block text-sm font-medium">
                Contact phone
              </label>
              <input id="phone" className={inputClass} value={draft.contactPhone} onChange={(e) => update({ contactPhone: e.target.value })} />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium">
                Staff notification email
              </label>
              <input id="email" type="email" className={inputClass} value={draft.staffNotificationEmail} onChange={(e) => update({ staffNotificationEmail: e.target.value })} />
            </div>
            <div>
              <label htmlFor="menu" className="block text-sm font-medium">
                Menu URL
              </label>
              <input id="menu" className={inputClass} value={draft.menuUrl} onChange={(e) => update({ menuUrl: e.target.value })} />
            </div>
            <div>
              <label htmlFor="max-party" className="block text-sm font-medium">
                Maximum online party size
              </label>
              <input id="max-party" type="number" min={1} className={inputClass} value={draft.maxOnlinePartySize} onChange={(e) => update({ maxOnlinePartySize: Number(e.target.value) })} />
            </div>
            <div>
              <label htmlFor="grace" className="block text-sm font-medium">
                Grace period (minutes)
              </label>
              <input id="grace" type="number" min={1} className={inputClass} value={draft.gracePeriodMinutes} onChange={(e) => update({ gracePeriodMinutes: Number(e.target.value) })} />
            </div>
            <div>
              <label htmlFor="entry-mode" className="block text-sm font-medium">
                Entry mode
              </label>
              <select id="entry-mode" className={inputClass} value={draft.entryMode} onChange={(e) => update({ entryMode: e.target.value as EntryMode })}>
                <option value="automatic">Automatic</option>
                <option value="staff_review">Staff review</option>
              </select>
            </div>
            <div className="flex items-center gap-3 pt-6">
              <input id="open" type="checkbox" className="h-5 w-5" checked={draft.waitlistOpen} onChange={(e) => update({ waitlistOpen: e.target.checked })} />
              <label htmlFor="open" className="text-sm font-medium">
                Waitlist open
              </label>
            </div>
          </div>
        </section>

        <section className="surface-card p-5">
          <h2 className="text-lg font-semibold">Default wait estimates</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Simple defaults per party class. Estimates are not guaranteed seating times.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-4">
            {(["A", "B", "C", "D"] as PartySizeClass[]).map((cls) => (
              <div key={cls}>
                <label htmlFor={`est-${cls}`} className="block text-sm font-medium">
                  Class {cls} (minutes)
                </label>
                <input
                  id={`est-${cls}`}
                  type="number"
                  min={0}
                  className={inputClass}
                  value={draft.defaultWaitEstimateMinutes[cls]}
                  onChange={(e) =>
                    update({
                      defaultWaitEstimateMinutes: {
                        ...draft.defaultWaitEstimateMinutes,
                        [cls]: Number(e.target.value),
                      },
                    })
                  }
                />
              </div>
            ))}
          </div>
        </section>

        <section className="surface-card p-5">
          <h2 className="text-lg font-semibold">Guest messages</h2>
          <div className="mt-4 space-y-4">
            {MESSAGE_FIELDS.map((field) => (
              <div key={field.key}>
                <label htmlFor={field.key} className="block text-sm font-medium">
                  {field.label}
                </label>
                <textarea
                  id={field.key}
                  rows={2}
                  className="mt-1 w-full rounded-md border border-input bg-card p-3 text-sm"
                  value={draft.messages[field.key]}
                  onChange={(e) => update({ messages: { ...draft.messages, [field.key]: e.target.value } })}
                />
              </div>
            ))}
          </div>
        </section>

        <section className="surface-card p-5">
          <h2 className="text-lg font-semibold">Guest message preview</h2>
          <div className="mt-4 space-y-3">
            {MESSAGE_FIELDS.map((field) => (
              <div key={field.key} className="rounded-md border border-border bg-muted p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {field.label}
                </p>
                <p className="mt-1 text-sm">{draft.messages[field.key]}</p>
              </div>
            ))}
          </div>
        </section>

        {error && (
          <p role="alert" className="text-sm font-medium text-destructive">
            Error: {error}
          </p>
        )}
        {saved && (
          <p role="status" className="text-sm font-medium">
            Settings saved.
          </p>
        )}

        <button
          type="submit"
          disabled={saving}
          className="h-11 rounded-md bg-primary px-6 font-medium text-primary-foreground disabled:opacity-60"
        >
          {saving ? "Saving…" : "Save settings"}
        </button>
      </form>
    </main>
  );
}
