// client/src/hooks/useOrganization.ts
import { useContext } from "react";
import { OrganizationContext } from "../contexts/OrganizationContext";

export function useOrganization() {
  const ctx = useContext(OrganizationContext);
  if (!ctx) throw new Error("useOrganization must be used within OrganizationProvider");
  return ctx;
}