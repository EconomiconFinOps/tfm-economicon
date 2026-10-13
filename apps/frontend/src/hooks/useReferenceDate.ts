import { useQuery } from "@tanstack/react-query";
import { fetchReferenceDate, getSessionGeneration } from "../services/api";

export function useReferenceDate(token: string) {
  return useQuery({
    queryKey: ["reference-date", getSessionGeneration()],
    queryFn: ({ signal }) => fetchReferenceDate(token, signal),
    enabled: Boolean(token),
    retry: false,
    staleTime: 60_000
  });
}
