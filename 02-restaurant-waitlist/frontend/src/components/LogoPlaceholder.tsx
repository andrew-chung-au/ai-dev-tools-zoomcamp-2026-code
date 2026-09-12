interface LogoPlaceholderProps {
  label: string;
  size?: "sm" | "md" | "lg";
}

/**
 * Neutral default logo placeholder. Real logo upload is deferred to the backend phase.
 */
export function LogoPlaceholder({ label, size = "md" }: LogoPlaceholderProps) {
  const dimension = size === "sm" ? "h-9 w-9 text-xs" : size === "lg" ? "h-20 w-20 text-lg" : "h-12 w-12 text-sm";
  return (
    <div
      role="img"
      aria-label={label}
      className={`${dimension} flex shrink-0 items-center justify-center rounded-md border border-border bg-secondary font-semibold uppercase tracking-widest text-secondary-foreground`}
    >
      Logo
    </div>
  );
}
