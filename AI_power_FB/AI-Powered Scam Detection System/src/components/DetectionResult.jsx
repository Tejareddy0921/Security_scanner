export default function DetectionResult({ result }) {
  if (!result) return null

  return (
    <section className={`result-card result-${result.level}`} aria-live="polite">
      <div className="result-heading">
        <span className="result-symbol" aria-hidden="true">{result.level === 'high' ? '!' : result.level === 'medium' ? '?' : '✓'}</span>
        <div>
          <span className="result-eyebrow">{result.level.toUpperCase()} RISK</span>
          <h2>{result.title}</h2>
          {result.category && <span className="result-category">Category: {result.category}</span>}
        </div>
        <div className="risk-score"><strong>{result.score === null ? '—' : `${result.score}%`}</strong><span>model confidence estimate</span></div>
      </div>
      <p className="confidence-note">The confidence estimate is not a calibrated probability.</p>
      {result.explanation && <p className="result-explanation">{result.explanation}</p>}
      {result.riskFactors?.length > 0 && (
        <div className="result-details">
          <h3>What we noticed</h3>
          <ul>{result.riskFactors.map((factor, index) => <li key={`${index}-${factor}`}>{factor}</li>)}</ul>
        </div>
      )}
      {result.recommendations?.length > 0 && (
        <div className="result-details result-next-steps">
          <h3>What to do next</h3>
          <ul>{result.recommendations.map((recommendation, index) => <li key={`${index}-${recommendation}`}>{recommendation}</li>)}</ul>
        </div>
      )}
      {!result.explanation && result.riskFactors?.length === 0 && result.recommendations?.length === 0 && (
        <p className="result-explanation">No additional details were returned for this check.</p>
      )}
      <div className="result-foot">{result.signals} risk factor{result.signals === 1 ? '' : 's'} identified</div>
    </section>
  )
}
