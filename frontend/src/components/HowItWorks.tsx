const steps = [
  'Upload your resume',
  'Add an internship',
  'Review your roadmap',
]

export function HowItWorks() {
  return (
    <section className="steps" id="how-it-works" aria-label="How it works">
      {steps.map((step, index) => (
        <div className="step" key={step}>
          <span>{index + 1}</span>
          <strong>{step}</strong>
        </div>
      ))}
    </section>
  )
}
