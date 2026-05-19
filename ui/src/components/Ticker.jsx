// ui/src/components/Ticker.jsx

const SIGNAL_COLORS = {
  BUY:   "#22c55e",
  SELL:  "#ef4444",
  WATCH: "#f97316",
  HOLD:  "#6b7280"
}

export default function Ticker({ items, gti }) {
  if (!items || items.length === 0) return null

  // duplicate items for seamless loop
  const doubled = [...items, ...items]

  return (
    <div className="ticker-wrap">
      <div className="ticker-gti">
        <span className="ticker-dot" />
        GTI {gti}
      </div>

      <div className="ticker-track">
        <div className="ticker-inner">
          {doubled.map((item, i) => (
            <div key={i} className="ticker-item">
              <span
                className="ticker-signal"
                style={{ color: SIGNAL_COLORS[item.signal] }}
              >
                {item.signal}
              </span>
              <span className="ticker-asset">{item.asset}</span>
              <span className="ticker-title">{item.title}</span>
              <span className="ticker-sep">◆</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}