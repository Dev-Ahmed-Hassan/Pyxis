import { useState } from 'react'
import { ExampleAnalysis } from '../components/ExampleAnalysis'
import { HowItWorks } from '../components/HowItWorks'
import { MatchInputPreview } from '../components/MatchInputPreview'
import { ProductStory } from '../components/ProductStory'
import { PublicFooter } from '../components/PublicFooter'
import { PublicHeader } from '../components/PublicHeader'
import type { FieldKey } from '../data/careerFields'

export function LandingPage() {
  const [selectedField, setSelectedField] =
    useState<FieldKey>('cybersecurity')

  return (
    <div className="app-shell">
      <PublicHeader />
      <main className="page-content">
        <section className="hero" aria-labelledby="hero-title">
          <h1 id="hero-title">Analyze your match.</h1>
          <p>
            Compare your resume with internship requirements using structured
            skill, evidence, and related-competency analysis.
          </p>
        </section>
        <MatchInputPreview />
        <HowItWorks />
        <ExampleAnalysis
          selectedField={selectedField}
          onFieldChange={setSelectedField}
        />
        <ProductStory key={selectedField} selectedField={selectedField} />
      </main>
      <PublicFooter />
    </div>
  )
}
