// ui/src/components/Globe.jsx
import { useEffect, useRef } from "react"
import * as d3 from "d3"
import * as topojson from "topojson-client"

const RISK_COLORS = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#3b82f6",
  low:      "#22c55e",
  none:     "#0d2137"
}

// numeric ID → our key
const ID_MAP = {
  "364": "iran",
  "643": "russia",
  "804": "ukraine",
  "376": "israel",
  "156": "china",
  "682": "saudi arabia",
  "840": "usa",
  "356": "india",
  "276": "germany",
  "250": "france",
  "826": "uk",
  "792": "turkey",
  "818": "egypt",
  "586": "pakistan",
  "784": "uae",
}

function getRiskColor(confidence) {
  if (!confidence || confidence === 0) return RISK_COLORS.none
  if (confidence >= 0.8) return RISK_COLORS.critical
  if (confidence >= 0.6) return RISK_COLORS.high
  if (confidence >= 0.35) return RISK_COLORS.medium
  return RISK_COLORS.low
}

export default function Globe({ countries, large }) {
  const svgRef = useRef(null)

  useEffect(() => {
    const svg    = d3.select(svgRef.current)
    const width  = large ? 900 : 650
    const height = large ? 600 : 450

    svg.attr("viewBox", `0 0 ${width} ${height}`)
       .style("background", "transparent")

    const projection = d3.geoNaturalEarth1()
      .scale(large ? 160 : 110)
      .translate([width / 2, height / 2])

    const path      = d3.geoPath().projection(projection)
    const graticule = d3.geoGraticule()

    svg.selectAll("*").remove()

    // grid lines
    svg.append("path")
      .datum(graticule())
      .attr("d", path)
      .attr("fill", "none")
      .attr("stroke", "rgba(0, 150, 255, 0.08)")
      .attr("stroke-width", 0.5)

    d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json")
      .then(world => {
        const geojson = topojson.feature(world, world.objects.countries)

        svg.selectAll(".country")
          .data(geojson.features)
          .enter()
          .append("path")
          .attr("class", "country")
          .attr("d", path)
          .attr("fill", d => {
            const id   = String(d.id)
            const key  = ID_MAP[id]
            const conf = key ? (countries[key] || 0) : 0
            return getRiskColor(conf)
          })
          .attr("stroke", "rgba(0, 150, 255, 0.2)")
          .attr("stroke-width", 0.5)
          .on("mouseover", function(event, d) {
            d3.select(this)
              .attr("stroke", "rgba(0, 200, 255, 0.8)")
              .attr("stroke-width", 1.5)
          })
          .on("mouseout", function() {
            d3.select(this)
              .attr("stroke", "rgba(0, 150, 255, 0.2)")
              .attr("stroke-width", 0.5)
          })

        // borders
        svg.append("path")
          .datum(topojson.mesh(world, world.objects.countries, (a, b) => a !== b))
          .attr("d", path)
          .attr("fill", "none")
          .attr("stroke", "rgba(0, 150, 255, 0.15)")
          .attr("stroke-width", 0.3)
      })
  }, [countries, large])

  return (
    <div className="globe-wrap">
      <svg ref={svgRef} style={{ width: "100%", height: "auto" }} />

      <div className="globe-legend">
        <div className="legend-title">RISK LEVEL</div>
        {[
          { label: "CRITICAL ≥80", color: RISK_COLORS.critical },
          { label: "HIGH ≥60",     color: RISK_COLORS.high     },
          { label: "MEDIUM ≥35",   color: RISK_COLORS.medium   },
          { label: "LOW <35",      color: RISK_COLORS.low      },
        ].map(item => (
          <div key={item.label} className="legend-item">
            <span className="legend-dot" style={{ background: item.color }} />
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      <div className="globe-hint">⊙ Hover any country to view market impact</div>
    </div>
  )
}