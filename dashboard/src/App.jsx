import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Cell,
} from "recharts";

const API = "";

const LEVELS = ["L0 Neutral", "L1 Mild", "L2 Knowledge", "L3 Authority",
                 "L4 Emotional", "L5 Social", "L6 Gaslighting", "L7 Meta"];

const SCORE_COLORS = {
  CLEAN_CORRECTION: "#22c55e",
  HEDGED_CORRECTION: "#86efac",
  COVERT_SYCOPHANCY: "#fb923c",
  HEDGED_SYCOPHANCY: "#f97316",
  EXPLICIT_SYCOPHANCY: "#ef4444",
  DEFLECTION: "#a78bfa",
  CONFUSED: "#facc15",
};

function RunList({ onSelect, selectedId }) {
  const [runs, setRuns] = useState([]);
  useEffect(() => {
    fetch(`${API}/api/runs/`).then(r => r.json()).then(setRuns).catch(() => {});
  }, []);

  return (
    <div style={{ width: 240, borderRight: "1px solid #2d2d2d", padding: "16px 8px", overflowY: "auto" }}>
      <h3 style={{ color: "#a1a1aa", fontSize: 12, textTransform: "uppercase", letterSpacing: 1, margin: "0 0 12px 8px" }}>Runs</h3>
      {runs.map(r => (
        <div key={r.id} onClick={() => onSelect(r.id)}
          style={{
            padding: "10px 12px", borderRadius: 6, cursor: "pointer", marginBottom: 4,
            background: selectedId === r.id ? "#1e293b" : "transparent",
            borderLeft: selectedId === r.id ? "2px solid #6366f1" : "2px solid transparent",
          }}>
          <div style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 500 }}>#{r.id} {r.target_model.split(":")[1]}</div>
          <div style={{ color: "#64748b", fontSize: 11, marginTop: 2 }}>{r.status} · {r.total_tests} tests</div>
          <div style={{ color: "#475569", fontSize: 11 }}>{r.created_at?.slice(0, 10)}</div>
        </div>
      ))}
    </div>
  );
}

function ScoreDistribution({ dist }) {
  const data = Object.entries(dist || {}).map(([score, pct]) => ({
    score: score.replace(/_/g, " "),
    pct: Math.round(pct * 100),
    fill: SCORE_COLORS[score] || "#64748b",
  })).sort((a, b) => b.pct - a.pct);

  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ color: "#a1a1aa", fontSize: 13, marginBottom: 12 }}>Score Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis type="number" tickFormatter={v => `${v}%`} stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis type="category" dataKey="score" stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} width={140} />
          <Tooltip formatter={v => `${v}%`} contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
          <Bar dataKey="pct" radius={[0, 3, 3, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ReportView({ runId }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!runId) return;
    setReport(null); setError(null);
    fetch(`${API}/api/reports/${runId}`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json(); })
      .then(setReport)
      .catch(e => setError(e.message));
  }, [runId]);

  if (!runId) return <div style={{ color: "#475569", padding: 40, textAlign: "center" }}>Select a run from the left</div>;
  if (error) return <div style={{ color: "#ef4444", padding: 40 }}>Error: {error}</div>;
  if (!report) return <div style={{ color: "#475569", padding: 40 }}>Loading...</div>;

  const claimTypes = Object.keys(report.curves || {});
  const CURVE_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];

  const multiCurveData = LEVELS.map((level, i) => {
    const point = { level };
    claimTypes.forEach(type => {
      point[type] = Math.round(((report.curves[type] || [])[i] || 0) * 1000) / 10;
    });
    return point;
  });

  return (
    <div style={{ padding: 32, overflowY: "auto", flex: 1 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 8 }}>
        <h2 style={{ color: "#e2e8f0", margin: 0 }}>Run #{runId} — {report.model}</h2>
        <span style={{ color: "#64748b", fontSize: 13 }}>{report.date}</span>
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 32, flexWrap: "wrap" }}>
        {[
          { label: "Sycophancy Rate", value: `${(report.overall_sycophancy_rate * 100).toFixed(1)}%`, color: report.overall_sycophancy_rate > 0.2 ? "#ef4444" : report.overall_sycophancy_rate > 0.1 ? "#f59e0b" : "#22c55e" },
          { label: "Break Point", value: `L${report.overall_break_point}`, color: "#a78bfa" },
          { label: "Covert Rate", value: `${(report.covert_sycophancy_rate * 100).toFixed(1)}%`, color: "#fb923c" },
          { label: "Claims Tested", value: report.claims_tested, color: "#94a3b8" },
          { label: "Controls", value: report.controls_tested, color: "#64748b" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, padding: "12px 20px", minWidth: 100 }}>
            <div style={{ color: "#64748b", fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
            <div style={{ color, fontSize: 22, fontWeight: 700, marginTop: 4 }}>{value}</div>
          </div>
        ))}
      </div>

      <h3 style={{ color: "#a1a1aa", fontSize: 13, marginBottom: 12 }}>Sycophancy Curve by Pressure Level</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={multiCurveData} margin={{ right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="level" stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis tickFormatter={v => `${v}%`} stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, 100]} />
          <Tooltip formatter={v => `${v}%`} contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
          <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
          {claimTypes.map((type, i) => (
            <Line key={type} type="monotone" dataKey={type} stroke={CURVE_COLORS[i % CURVE_COLORS.length]}
              strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <ScoreDistribution dist={report.response_distribution} />

      {Object.keys(report.category_break_points || {}).length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ color: "#a1a1aa", fontSize: 13, marginBottom: 12 }}>Break Points by Claim Type</h3>
          <div style={{ display: "flex", gap: 12 }}>
            {Object.entries(report.category_break_points).map(([type, bp]) => (
              <div key={type} style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, padding: "10px 16px" }}>
                <div style={{ color: "#64748b", fontSize: 11, textTransform: "uppercase" }}>{type}</div>
                <div style={{ color: "#a78bfa", fontSize: 20, fontWeight: 700 }}>L{bp}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [selectedRun, setSelectedRun] = useState(null);

  return (
    <div style={{ display: "flex", height: "100vh", background: "#020617", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <div style={{ width: 240, flexShrink: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "20px 16px 12px", borderBottom: "1px solid #1e293b" }}>
          <div style={{ color: "#e2e8f0", fontWeight: 700, fontSize: 16 }}>Probe</div>
          <div style={{ color: "#475569", fontSize: 11, marginTop: 2 }}>AI Sycophancy Detection</div>
        </div>
        <RunList onSelect={setSelectedRun} selectedId={selectedRun} />
      </div>
      <ReportView runId={selectedRun} />
    </div>
  );
}
