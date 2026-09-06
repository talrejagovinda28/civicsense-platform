"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth, UserButton } from "@clerk/nextjs";
import { useState } from "react";

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
  const { draft, canProceed, resetDraft } = useComplaintWizard();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const currentStep = stepFromPathname(pathname);
  if (!currentStep) {
    return (
      <main className="mx-auto min-h-screen max-w-2xl px-6 py-12">
        <p className="text-neutral-600">Invalid wizard step.</p>
        <Link href="/complaints/new/location" className="mt-4 inline-block underline">
          Start over
        </Link>
      </main>
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
      await createComplaint(token, payload);
      resetDraft();
      router.push("/complaints?submitted=1");
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Failed to submit complaint.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto min-h-screen max-w-2xl px-6 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-neutral-500 hover:text-neutral-700">
            CivicSense
          </Link>
          <h1 className="mt-1 text-2xl font-bold">Raise Complaint</h1>
          <p className="mt-1 text-sm text-neutral-600">{stepConfig.description}</p>
        </div>
        <UserButton />
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
                    isActive || isComplete ? "bg-neutral-900" : "bg-neutral-200"
                  }`}
                />
                <p
                  className={`mt-2 text-xs ${
                    isActive ? "font-semibold text-neutral-900" : "text-neutral-500"
                  }`}
                >
                  {step.label}
                </p>
              </li>
            );
          })}
        </ol>
      </nav>

      <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">{stepConfig.label}</h2>
        <div className="mt-6">{children}</div>
      </section>

      <footer className="mt-6 flex items-center justify-between gap-4">
        {previousStep ? (
          <button
            type="button"
            onClick={() => router.push(getStepConfig(previousStep).path)}
            disabled={submitting}
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium"
          >
            Back
          </button>
        ) : (
          <Link
            href="/"
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium"
          >
            Cancel
          </Link>
        )}

        <div className="flex flex-col items-end gap-2">
          {!canContinue && validationMessage && (
            <p className="text-xs text-neutral-500">{validationMessage}</p>
          )}
          {submitError && <p className="text-xs text-red-600">{submitError}</p>}

          {nextStep ? (
            <button
              type="button"
              disabled={!canContinue}
              onClick={() => router.push(getStepConfig(nextStep).path)}
              className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              Continue
            </button>
          ) : (
            <button
              type="button"
              disabled={!canContinue || submitting}
              onClick={handleSubmit}
              className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {submitting ? "Submitting…" : "Submit Complaint"}
            </button>
          )}
        </div>
      </footer>
    </main>
  );
}
