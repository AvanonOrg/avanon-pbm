interface Props {
  status: string;
  progress?: number;
  currentStep?: string;
}

export function TaskStatusBadge({ status, progress, currentStep }: Props) {
  if (status === "complete" || !status) return null;

  const color = status === "running" ? "#3b82f6" : status === "failed" ? "#ef4444" : "#94a3b8";

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "4px 10px",
        border: `1px solid ${color}`,
        borderRadius: 999,
        fontSize: 12,
        color,
        marginTop: 8,
      }}
    >
      {status === "running" && (
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: color,
            animation: "pulse 1.5s infinite",
          }}
        />
      )}
      <span style={{ fontWeight: 600 }}>{status.toUpperCase()}</span>
      {currentStep && <span style={{ color: "#94a3b8" }}>· {currentStep}</span>}
      {progress != null && progress > 0 && status === "running" && (
        <span style={{ color: "#94a3b8" }}>{progress}%</span>
      )}
    </div>
  );
}
