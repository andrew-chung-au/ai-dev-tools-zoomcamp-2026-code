export function formatTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function formatDate(dateString: string): string {
  const d = new Date(`${dateString}T00:00:00`);
  return d.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" });
}

export function minutesSince(iso: string): number {
  return Math.round((Date.now() - new Date(iso).getTime()) / 60_000);
}
