import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ScorePoint } from "../types";

export function ScoreChart({ history }: { history: ScorePoint[] }) {
  if (history.length === 0) {
    return <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>No score history available yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={history} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
        <CartesianGrid stroke="var(--gridline)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "var(--text-muted)" }}
          axisLine={{ stroke: "var(--baseline)" }}
          tickLine={false}
          minTickGap={30}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: "var(--text-muted)" }}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--text-primary)",
          }}
          labelStyle={{ color: "var(--text-secondary)" }}
        />
        <Line
          type="monotone"
          dataKey="score"
          stroke="var(--series-1)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
