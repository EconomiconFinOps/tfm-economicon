import { useEffect, useState } from "react";
import {
  fetchBillingSummary,
  fetchHealth,
  fetchProfile,
  fetchTenants
} from "../services/api";

export function useDashboardData() {
  const [state, setState] = useState({
    loading: true,
    error: null,
    payload: null
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [profile, tenants, billing, health] = await Promise.all([
          fetchProfile(),
          fetchTenants(),
          fetchBillingSummary(),
          fetchHealth()
        ]);

        if (!cancelled) {
          setState({
            loading: false,
            error: null,
            payload: { profile, tenants, billing, health }
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            loading: false,
            error: error.message,
            payload: null
          });
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

