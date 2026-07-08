/**
 * SourceTooltip.jsx
 *
 * Hover tooltip that shows the source document and section for any metric.
 * Directly addresses the brief's "stand over the outputs" requirement —
 * every number on the dashboard has a visible audit trail.
 *
 * Usage:
 *   <SourceTooltip source="Senus PLC Information Document, Dec 2025, Section 7.1" />
 */
import React, { useState } from 'react'

export default function SourceTooltip({ source }) {
  const [visible, setVisible] = useState(false)

  if (!source) return null

  return (
    <span
      className="source-anchor"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      tabIndex={0}
      aria-label={`Source: ${source}`}
    >
      <span className="source-icon">⌗</span>
      {visible && (
        <span className="source-tooltip" role="tooltip">
          <span className="source-tooltip-label">Source</span>
          {source}
        </span>
      )}
    </span>
  )
}
