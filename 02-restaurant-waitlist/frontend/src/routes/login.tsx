import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { waitlistService } from "@/services";
import { setSession } from "@/lib/session";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Staff sign in — Demo Restaurant Waitlist" },
      {
        name: "description",
        content: "Mocked staff sign in for the Demo Restaurant walk-in waitlist prototype.",
      },
      { property: "og:title", content: "Staff sign in — Demo Restaurant Waitlist" },
      {
        property: "og:description",
        content: "Mocked staff sign in for the walk-in waitlist prototype.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ username?: string; password?: string; form?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const nextErrors: typeof errors = {};
    if (!username.trim()) nextErrors.username = "Enter your username or email.";
    if (!password.trim()) nextErrors.password = "Enter your password.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const session = await waitlistService.login({ username, password });
      setSession(session);
      navigate({ to: "/staff" });
    } catch (error) {
      setErrors({ form: error instanceof Error ? error.message : "Sign in failed." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-5 py-10">
      <div className="surface-card p-6">
        <h1 className="text-2xl font-semibold">Staff sign in</h1>
        <p className="mt-2 rounded-md border border-border bg-info-surface p-3 text-sm">
          Authentication is mocked for this frontend prototype. Any non-empty username and password
          will sign you in. No credentials are stored.
        </p>

        <form onSubmit={onSubmit} noValidate className="mt-6 space-y-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium">
              Username or email
            </label>
            <input
              id="username"
              name="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              aria-invalid={Boolean(errors.username)}
              aria-describedby={errors.username ? "username-error" : undefined}
              className="mt-1 h-11 w-full rounded-md border border-input bg-card px-3 text-base"
            />
            {errors.username && (
              <p id="username-error" className="mt-1 text-sm font-medium text-destructive">
                Error: {errors.username}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? "password-error" : undefined}
              className="mt-1 h-11 w-full rounded-md border border-input bg-card px-3 text-base"
            />
            {errors.password && (
              <p id="password-error" className="mt-1 text-sm font-medium text-destructive">
                Error: {errors.password}
              </p>
            )}
          </div>

          {errors.form && (
            <p role="alert" className="text-sm font-medium text-destructive">
              Error: {errors.form}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="h-11 w-full rounded-md bg-primary px-4 font-medium text-primary-foreground disabled:opacity-60"
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </main>
  );
}
