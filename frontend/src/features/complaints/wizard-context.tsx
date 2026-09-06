"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import {
  ComplaintDraft,
  ComplaintWizardStep,
  emptyComplaintDraft,
} from "./types";
import { validateStep } from "./wizard-steps";

type ComplaintWizardContextValue = {
  draft: ComplaintDraft;
  updateDraft: (patch: Partial<ComplaintDraft>) => void;
  resetDraft: () => void;
  canProceed: (step: ComplaintWizardStep) => boolean;
};

const ComplaintWizardContext = createContext<ComplaintWizardContextValue | null>(
  null,
);

export function ComplaintWizardProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [draft, setDraft] = useState<ComplaintDraft>(emptyComplaintDraft);

  const updateDraft = useCallback((patch: Partial<ComplaintDraft>) => {
    setDraft((current) => ({ ...current, ...patch }));
  }, []);

  const resetDraft = useCallback(() => {
    setDraft(emptyComplaintDraft());
  }, []);

  const value = useMemo<ComplaintWizardContextValue>(
    () => ({
      draft,
      updateDraft,
      resetDraft,
      canProceed: (step) => validateStep(step, draft),
    }),
    [draft, updateDraft, resetDraft],
  );

  return (
    <ComplaintWizardContext.Provider value={value}>
      {children}
    </ComplaintWizardContext.Provider>
  );
}

export function useComplaintWizard() {
  const context = useContext(ComplaintWizardContext);
  if (!context) {
    throw new Error("useComplaintWizard must be used within ComplaintWizardProvider");
  }
  return context;
}
