import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { login } from "../services/api";

export function LoginPage({ onLogin }) {
  const [form, setForm] = useState({
    email: "operator@finops.local",
    password: "secret"
  });

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: onLogin
  });

  function handleSubmit(event) {
    event.preventDefault();
    mutation.mutate(form);
  }

  return (
    <div className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">Operator login</p>
        <h1>Access the tenant control tower</h1>
        <p className="auth-copy">
          This demo build uses the seeded operator account so the team can validate
          auth, tenant isolation and assistant flows end-to-end.
        </p>

        <form className="form-stack" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="login-email">Email</label>
          <input
            id="login-email"
            className="text-input"
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
          />

          <label className="field-label" htmlFor="login-password">Password</label>
          <input
            id="login-password"
            className="text-input"
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
          />

          {mutation.error ? <p className="error-copy">{mutation.error.message}</p> : null}

          <button className="primary-button" type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </div>
  );
}
