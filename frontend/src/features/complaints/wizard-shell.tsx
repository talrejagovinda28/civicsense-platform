"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { useCity } from "@/features/cities/city-context";
import { AppHeader } from "@/features/shared/app-header";
import { createComplaint } from "@/lib/api";

import { buildCreateComplaintPayload } from "./build-payload";
import {
  getNextStep,
  getPreviousStep,
  getStepConfig,
  getStepIndex,
  getStepValidationMessage,
  stepFromPathname,
  WIZARD_STEP_CONFIG,
} from "./wizard-steps";
import { useComplaintWizard } from "./wizard-context";

export function WizardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { getToken } = useAuth();
  const { selectedCity, isReportingEnabled, isLoading: cityLoading } = useCity();
  const { draft, canProceed, resetDraft, updateDraft } = useComplaintWizard();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedCity) {
      updateDraft({
        city: selectedCity.name,
        citySlug: selectedCity.slug,
      });
    }
  }, [selectedCity, updateDraft]);

  const currentStep = stepFromPathname(pathname);
  if (!currentStep) {
    return (
      <main className="mx-auto min-h-screen max-w-2xl px-6 py-12">
        <p className="text-[var(--muted)]">Invalid wizard step.</p>
        <Link href="/complaints/new/location" className="mt-4 inline-block underline">
          Start over
        </Link>
      </main>
    );
  }

  // While city config loads, keep the shell mounted so MapLibre is not torn down
  // and remounted (that remount + click race caused client crashes on Preview).
  if (cityLoading) {
    return (
      <>
        <AppHeader />
        <main className="mx-auto max-w-lg px-6 py-16 text-center">
          <p className="text-sm text-[var(--muted)]">Loading city settings…</p>
        </main>
      </>
    );
  }

  if (!isReportingEnabled) {
    return (
      <>
        <AppHeader />
        <main className="mx-auto max-w-lg px-6 py-16 text-center">
          <h1 className="text-2xl font-bold text-civic-navy">Reporting unavailable</h1>
          <p className="mt-3 text-[var(--muted)]">
            Complaint reporting is not yet enabled for {selectedCity?.name ?? "this city"}.
          </p>
          <Link
            href="/"
            className="mt-6 inline-block rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
          >
            Back to map
          </Link>
        </main>
      </>
    );
  }

  const stepConfig = getStepConfig(currentStep);
  const stepIndex = getStepIndex(currentStep);
  const nextStep = getNextStep(currentStep);
  const previousStep = getPreviousStep(currentStep);
  const canContinue = canProceed(currentStep);
  const validationMessage = getStepValidationMessage(currentStep, draft);

  const handleSubmit = async () => {
    if (!canContinue || submitting) {
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("You must be signed in to submit a complaint.");
      }

      const payload = buildCreateComplaintPayload(draft);
      const created = await createComplaint(token, payload);
      resetDraft();
      router.push(`/complaints/${created.id}?submitted=1`);
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Failed to submit complaint.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <AppHeader showCitySelector={false} />
      <main className="mx-auto min-h-screen max-w-2xl px-6 py-8">
        <header className="mb-8">
          <Link href="/" className="text-sm text-[var(--muted)] hover:text-civic-navy">
            ← Back to map
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-civic-navy">Raise Complaint</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {selectedCity?.name ?? draft.city} · {stepConfig.description}
          </p>
        </header>

        <nav aria-label="Wizard progress" className="mb-8">
          <ol className="flex gap-2">
            {WIZARD_STEP_CONFIG.map((step, index) => {
              const isActive = index === stepIndex;
              const isComplete = index < stepIndex;

              return (
                <li key={step.id} className="flex-1">
                  <div
                    className={`h-1 rounded-full ${
                      isActive || isComplete
                        ? "bg-[var(--primary)]"
                        : "bg-[var(--border)]"
                    }`}
                  />
                  <p
                    className={`mt-2 text-xs ${
                      isActive ? "font-semibold text-civic-navy" : "text-[var(--muted)]"
                    }`}
                  >
                    {step.label}
                  </p>
                </li>
              );
            })}
          </ol>
        </nav>

        <section className="rounded-xl border border-civic bg-[var(--surface)] p-6 shadow-civic-sm">
          <h2 className="text-lg font-semibold text-civic-navy">{stepConfig.label}</h2>
          <div className="mt-6">{children}</div>
        </section>

        <footer className="mt-6 flex items-center justify-between gap-4">
          {previousStep ? (
            <button
              type="button"
              onClick={() => router.push(getStepConfig(previousStep).path)}
              disabled={submitting}
              className="rounded-lg border border-civic px-4 py-2 text-sm font-medium"
            >
              Back
            </button>
          ) : (
            <Link
              href="/"
              className="rounded-lg border border-civic px-4 py-2 text-sm font-medium"
            >
              Cancel
            </Link>
          )}

          <div className="flex flex-col items-end gap-2">
            {!canContinue && validationMessage && (
              <p className="text-xs text-[var(--muted)]">{validationMessage}</p>
            )}
            {submitError && <p className="text-xs text-red-600">{submitError}</p>}

            {nextStep ? (
              <button
                type="button"
                disabled={!canContinue}
                onClick={() => router.push(getStepConfig(nextStep).path)}
                className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                Continue
              </button>
            ) : (
              <button
                type="button"
                disabled={!canContinue || submitting}
                onClick={handleSubmit}
                className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? "Submitting…" : "Submit Complaint"}
              </button>
            )}
          </div>
        </footer>
      </main>
    </>
  );
}
