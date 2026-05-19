// ui/src/components/RiskMeter.jsx

const LEVEL_COLORS = {
  CRITICAL: "#ef4444",
  HIGH:     "#f97316",
  MEDIUM:   "#3b82f6",
  LOW:      "#22c55e"
}

export default function RiskMeter({ gti, level }) {
  const color = LEVEL_COLORS[level] || "#22c55e"
  const angle = (gti / 100) * 180

  return (
    <div className="risk-meter">
      <div className="meter-title">GEOPOLITICAL THREAT INDEX</div>

      {/* semicircle gauge */}
      <div className="gauge-wrap">
        <svg viewBox="0 0 200 110" className="gauge-svg">
          {/* background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* colored arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${(gti / 100) * 251} 251`}
            style={{ transition: "stroke-dasharray 1s ease, stroke 0.5s ease" }}
          />
          {/* needle */}
          <line
            x1="100"
            y1="100"
            x2={100 + 65 * Math.cos(((180 - angle) * Math.PI) / 180)}
            y2={100 - 65 * Math.sin(((180 - angle) * Math.PI) / 180)}
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            style={{ transition: "all 1s ease" }}
          />
          <circle cx="100" cy="100" r="5" fill="white" />
        </svg>

        <div className="gti-score" style={{ color }}>
          {gti}
        </div>
      </div>

      <div className="level-badge" style={{
        background: color + "22",
        color,
        border: `1px solid ${color}44`
      }}>
        {level}
      </div>

      {/* risk scale */}
      <div className="risk-scale">
        {[
          { label: "LOW",      range: "<35",  color: "#22c55e" },
          { label: "MEDIUM",   range: "≥35",  color: "#3b82f6" },
          { label: "HIGH",     range: "≥60",  color: "#f97316" },
          { label: "CRITICAL", range: "≥80",  color: "#ef4444" },
        ].map(item => (
          <div key={item.label} className="scale-item">
            <span className="scale-dot" style={{ background: item.color }} />
            <span className="scale-label">{item.label}</span>
            <span className="scale-range">{item.range}</span>
          </div>
        ))}
      </div>
    </div>
  )
}