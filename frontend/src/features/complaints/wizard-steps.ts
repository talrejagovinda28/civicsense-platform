import {
  COMPLAINT_WIZARD_STEPS,
  ComplaintDraft,
  ComplaintWizardStep,
} from "./types";

export type WizardStepConfig = {
  id: ComplaintWizardStep;
  path: string;
  label: string;
  description: string;
};

export const WIZARD_STEP_CONFIG: WizardStepConfig[] = [
  {
    id: "location",
    path: "/complaints/new/location",
    label: "Location",
    description: "Pin where the issue is",
  },
  {
    id: "photo",
    path: "/complaints/new/photo",
    label: "Photo",
    description: "Take or upload a photo",
  },
  {
    id: "category",
    path: "/complaints/new/category",
    label: "Category",
    description: "Confirm the issue type",
  },
  {
    id: "description",
    path: "/complaints/new/description",
    label: "Description",
    description: "Describe the problem",
  },
  {
    id: "review",
    path: "/complaints/new/review",
    label: "Review",
    description: "Check and submit",
  },
];

export function getStepConfig(step: ComplaintWizardStep): WizardStepConfig {
  const config = WIZARD_STEP_CONFIG.find((item) => item.id === step);
  if (!config) {
    throw new Error(`Unknown wizard step: ${step}`);
  }
  return config;
}

export function getStepIndex(step: ComplaintWizardStep): number {
  return COMPLAINT_WIZARD_STEPS.indexOf(step);
}

export function getNextStep(
  step: ComplaintWizardStep,
): ComplaintWizardStep | null {
  const index = getStepIndex(step);
  return COMPLAINT_WIZARD_STEPS[index + 1] ?? null;
}

export function getPreviousStep(
  step: ComplaintWizardStep,
): ComplaintWizardStep | null {
  const index = getStepIndex(step);
  return index > 0 ? COMPLAINT_WIZARD_STEPS[index - 1] : null;
}

export function stepFromPathname(pathname: string): ComplaintWizardStep | null {
  const match = WIZARD_STEP_CONFIG.find((item) => item.path === pathname);
  return match?.id ?? null;
}

export function validateStep(
  step: ComplaintWizardStep,
  draft: ComplaintDraft,
): boolean {
  switch (step) {
    case "location":
      return (
        draft.latitude !== null &&
        draft.longitude !== null &&
        Boolean(draft.googlePlaceId) &&
        Boolean(draft.address)
      );
    case "photo":
      return draft.images.length >= 1;
    case "category":
      return Boolean(draft.categoryId);
    case "description":
      return draft.description.trim().length >= 20;
    case "review":
      return COMPLAINT_WIZARD_STEPS.slice(0, -1).every((item) =>
        validateStep(item, draft),
      );
    default:
      return false;
  }
}

export function getStepValidationMessage(
  step: ComplaintWizardStep,
  draft: ComplaintDraft,
): string | null {
  if (validateStep(step, draft)) {
    return null;
  }

  switch (step) {
    case "location":
      return "Set a location with address and map pin.";
    case "photo":
      return "Add at least one photo.";
    case "category":
      return "Select a category.";
    case "description":
      return "Description must be at least 20 characters.";
    case "review":
      return "Complete all previous steps before submitting.";
    default:
      return "Complete this step to continue.";
  }
}
