import type { ButtonHTMLAttributes, ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cx("card p-6 ease", className)}>{children}</section>;
}

export function Label({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cx("label", className)}>{children}</p>;
}

type Variant = "primary" | "ghost" | "quiet";

export function Button({ variant = "ghost", className, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      {...props}
      className={cx(
        "ease inline-flex items-center justify-center gap-2 rounded-full px-4 py-2 text-sm font-medium",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-button text-button-ink shadow-[var(--shadow-soft)] hover:brightness-110",
        variant === "ghost" && "border border-line text-ink hover:border-terracotta hover:bg-card-soft",
        variant === "quiet" && "text-ink-2 hover:text-ink",
        className,
      )}
    />
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: T; label: string; disabled?: boolean }[];
  value: T;
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-full border border-line bg-card-soft p-1">
      {options.map((o) => (
        <button
          key={o.value}
          role="radio"
          aria-checked={o.value === value}
          disabled={o.disabled}
          onClick={() => onChange(o.value)}
          className={cx(
            "ease rounded-full px-3 py-1 text-xs font-semibold tracking-wide",
            o.value === value ? "bg-button text-button-ink" : "text-ink-2 hover:text-ink",
            o.disabled && "cursor-not-allowed opacity-40",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded-xl bg-card-soft", className)} />;
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-ink-2">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-terracotta border-t-transparent" />
      {label}
    </span>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-2xl border border-rosewood/60 bg-card-soft p-5">
      <p className="font-display text-xl">Something went wrong</p>
      <p className="mt-1 text-sm text-ink-2">{message}</p>
      {onRetry && (
        <Button className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line p-8 text-center">
      <p className="font-display text-2xl">{title}</p>
      {children && <div className="mt-2 text-sm text-ink-2">{children}</div>}
    </div>
  );
}

export function pct(x: number | null | undefined, digits = 1) {
  return x === null || x === undefined ? "n/a" : `${(100 * x).toFixed(digits)}%`;
}
