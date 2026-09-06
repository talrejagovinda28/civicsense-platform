type StatusRow = {
  label: string;
  value: string;
};

type StatusCardProps = {
  title: string;
  loading?: boolean;
  error?: string;
  rows: StatusRow[];
};

export function StatusCard({
  title,
  loading = false,
  error,
  rows,
}: StatusCardProps) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold">{title}</h2>
      {loading && <p className="mt-3 text-sm text-neutral-500">Loading…</p>}
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {!loading && !error && (
        <dl className="mt-3 space-y-2">
          {rows.map((row) => (
            <div key={row.label}>
              <dt className="text-xs uppercase tracking-wide text-neutral-500">
                {row.label}
              </dt>
              <dd className="break-all text-sm font-medium">{row.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
