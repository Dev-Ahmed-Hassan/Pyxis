type PlaceholderPageProps = {
  title: string
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <main className="app-page">
      <header className="app-page-header">
        <div>
          <span className="app-page-eyebrow">Frontend module</span>
          <h1>{title}</h1>
          <p>
            This route is reserved in the application shell. Its backend
            workflow will be connected in the next focused frontend pass.
          </p>
        </div>
      </header>
    </main>
  )
}
