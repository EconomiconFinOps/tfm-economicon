export function AppShell({ activeView, items, onSelect, children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">FinOps Assistant</p>
          <h1>Control Tower</h1>
          <p className="sidebar-copy">
            Opera costes, tenants y pipelines desde una misma superficie.
          </p>
        </div>

        <nav className="nav">
          {items.map((item) => (
            <button
              key={item.id}
              className={item.id === activeView ? "nav-item active" : "nav-item"}
              onClick={() => onSelect(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="content">{children}</main>
    </div>
  );
}

