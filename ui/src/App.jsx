// ui/src/App.jsx
import { useState, useEffect } from "react"
import Globe from "./components/Globe"
import SignalFeed from "./components/SignalFeed"
import Ticker from "./components/Ticker"
import RiskMeter from "./components/RiskMeter"
import "./styles.css"

const API = "http://localhost:8000"

export default function App() {
  const [signals, setSignals]     = useState([])
  const [risk, setRisk]           = useState({ gti: 0, level: "LOW" })
  const [countries, setCountries] = useState({})
  const [ticker, setTicker]       = useState([])
  const [activeTab, setActiveTab] = useState("pulse")

  const fetchData = async () => {
    try {
      const [s, r, c, t] = await Promise.all([
        fetch(`${API}/signals`).then(r => r.json()),
        fetch(`${API}/risk`).then(r => r.json()),
        fetch(`${API}/countries`).then(r => r.json()),
        fetch(`${API}/ticker`).then(r => r.json())
      ])
      setSignals(s)
      setRisk(r)
      setCountries(c)
      setTicker(t)
    } catch (e) {
      console.error("API error:", e)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      {/* stars background */}
      <div className="stars" />

      {/* navbar */}
      <nav className="navbar">
        <div className="nav-brand">
          <span className="nav-icon">⚡</span>
          <div>
            <div className="nav-title">GEOTRADE</div>
            <div className="nav-sub">TRADER v2.0</div>
          </div>
        </div>

        <div className="nav-tabs">
          {[
            { id: "pulse",   label: "EARTH PULSE" },
            { id: "signals", label: "AI SIGNALS"  },
            { id: "map",     label: "GEO MAP"      },
          ].map(tab => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="nav-live">
          <span className="live-dot" />
          LIVE
        </div>
      </nav>

      {/* main content */}
      <main className="main">
        {activeTab === "pulse" && (
          <div className="pulse-view">
            <Globe countries={countries} />
            <div className="side-panel">
              <RiskMeter gti={risk.gti} level={risk.level} />
              <SignalFeed signals={signals.slice(0, 5)} />
            </div>
          </div>
        )}

        {activeTab === "signals" && (
          <div className="signals-view">
            <SignalFeed signals={signals} full />
          </div>
        )}

        {activeTab === "map" && (
          <div className="map-view">
            <Globe countries={countries} large />
          </div>
        )}
      </main>

      {/* bottom ticker */}
      <Ticker items={ticker} gti={risk.gti} />
    </div>
  )
}