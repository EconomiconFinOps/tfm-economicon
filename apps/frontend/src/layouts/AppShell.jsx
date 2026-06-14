export function AppShell({
  activeView,
  items,
  onSelect,
  user,
  tenants,
  activeTenantId,
  onTenantChange,
  onLogout,
  children
}) {
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

        <div className="tenant-panel">
          <label className="field-label" htmlFor="tenant-selector">Active tenant</label>
          <select
            id="tenant-selector"
            className="tenant-select"
            value={activeTenantId}
            onChange={(event) => onTenantChange(event.target.value)}
          >
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </div>

        <div className="session-panel">
          <div>
            <p className="eyebrow">Signed in</p>
            <strong>{user.full_name}</strong>
            <p className="session-copy">{user.email}</p>
          </div>
          <button className="ghost-button" type="button" onClick={onLogout}>
            Logout
          </button>
        </div>
      </aside>

      <main className="content">{children}</main>
    </div>
  );
}
