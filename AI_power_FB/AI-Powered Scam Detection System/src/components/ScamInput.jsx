export default function ScamInput({ value, onChange, onSubmit, isLoading = false }) {
  return (
    <form className="scan-form" onSubmit={onSubmit}>
      <label className="field-label" htmlFor="message-to-check">Message or link</label>
      <textarea
        id="message-to-check"
        className="message-field"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={'Paste a suspicious text, email, or link here…\n\nFor example: “Your package is on hold. Pay now to release it.”'}
        rows={7}
        maxLength={5000}
        required
      />
      <div className="scan-form-footer">
        <span>{value.length.toLocaleString()} / 5,000 characters</span>
        <button className="button button-primary" type="submit" disabled={isLoading || !value.trim()}>
          {isLoading ? 'Checking…' : 'Check for scams'} <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  )
}
