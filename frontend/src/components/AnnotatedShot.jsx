import { useState } from 'react'

/**
 * One inspection photo with the model's bounding boxes drawn over it.
 *
 * The boxes come back in the pixel coordinates of the image the model analysed,
 * so the SVG uses that as its viewBox and scales with the rendered <img>. That
 * keeps the boxes aligned at any display size without any manual maths.
 */
export default function AnnotatedShot({ image, colours, activeId, onHover }) {
  const [natural, setNatural] = useState(null)

  const width = image.dimensions?.width || natural?.width || 0
  const height = image.dimensions?.height || natural?.height || 0
  const ready = width > 0 && height > 0

  return (
    <div
      className="shot"
      onMouseLeave={() => onHover?.(null)}
    >
      <img
        src={image.secure_url}
        alt={image.view_angle || 'inspection photo'}
        loading="lazy"
        onLoad={(event) =>
          setNatural({
            width: event.currentTarget.naturalWidth,
            height: event.currentTarget.naturalHeight,
          })
        }
      />

      {ready && image.detections.length > 0 && (
        <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          {image.detections.map((found) => {
            const colour = colours[found.class_key] || '#38bdf8'
            const box = found.bbox
            if (!box) return null
            const active = activeId === found.id
            const labelText = `${found.label} ${(found.confidence * 100).toFixed(0)}%`
            // Keep the label inside the frame when the box hugs the top edge.
            const labelAbove = box.y > height * 0.05
            const labelY = labelAbove ? box.y - 6 : box.y + 20

            return (
              <g key={found.id} style={{ color: colour }}>
                <rect
                  className={`box-rect${active ? ' active' : ''}`}
                  x={box.x}
                  y={box.y}
                  width={box.width}
                  height={box.height}
                  stroke={colour}
                  style={{ pointerEvents: 'all' }}
                  onMouseEnter={() => onHover?.(found.id)}
                />
                <rect
                  className="box-label-bg"
                  x={box.x}
                  y={labelY - 13}
                  width={labelText.length * 7.2 + 10}
                  height={17}
                  fill={colour}
                />
                <text className="box-label" x={box.x + 5} y={labelY}>
                  {labelText}
                </text>
              </g>
            )
          })}
        </svg>
      )}
    </div>
  )
}
