// ui/src/components/SignalFeed.jsx

const SIGNAL_COLORS = {
  BUY:   "#22c55e",
  SELL:  "#ef4444",
  WATCH: "#f97316",
  HOLD:  "#6b7280"
}

const ASSET_ICONS = {
  Oil:         "🛢️",
  Gold:        "🥇",
  Wheat:       "🌾",
  Commodities: "📦",
  Currency:    "💱",
  None:        "📊"
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function SignalFeed({ signals, full }) {
  if (!signals || signals.length === 0) {
    return (
      <div className="signal-feed">
        <div className="feed-title">AI SIGNALS</div>
        <div className="feed-empty">No signals yet — run main.py to generate</div>
      </div>
    )
  }

  return (
    <div className={`signal-feed ${full ? "full" : ""}`}>
      <div className="feed-title">
        AI SIGNALS
        <span className="feed-count">{signals.length}</span>
      </div>

      <div className="feed-list">
        {signals.map((s, i) => (
          <div key={i} className="signal-card">
            <div className="signal-top">
              <div className="signal-asset">
                <span className="asset-icon">{ASSET_ICONS[s.asset] || "📊"}</span>
                <span className="asset-name">{s.asset}</span>
              </div>
              <span
                className="signal-badge"
                style={{ background: SIGNAL_COLORS[s.signal] + "22",
                         color:      SIGNAL_COLORS[s.signal],
                         border:     `1px solid ${SIGNAL_COLORS[s.signal]}44` }}
              >
                {s.signal}
              </span>
            </div>

            <div className="signal-title">{s.title}</div>

            <div className="signal-bottom">
              <div className="signal-conf">
                <div className="conf-bar">
                  <div
                    className="conf-fill"
                    style={{
                      width:      `${s.confidence * 100}%`,
                      background: SIGNAL_COLORS[s.signal]
                    }}
                  />
                </div>
                <span>{Math.round(s.confidence * 100)}%</span>
              </div>
              <span className="signal-time">{timeAgo(s.created_at)}</span>
            </div>

            {s.countries && s.countries.length > 0 && (
              <div className="signal-countries">
                {s.countries.slice(0, 3).map((c, j) => (
                  <span key={j} className="country-tag">{c}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}