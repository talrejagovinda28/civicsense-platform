"use client";

import { useComplaintWizard } from "../wizard-context";

export function DescriptionStep() {
  const { draft, updateDraft } = useComplaintWizard();

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium">
        What is the issue?
        <textarea
          value={draft.description}
          onChange={(event) => updateDraft({ description: event.target.value })}
          rows={6}
          placeholder="Describe the civic issue in detail (minimum 20 characters)..."
          className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
        />
      </label>
      <p className="text-xs text-neutral-500">
        {draft.description.trim().length}/20 characters minimum
      </p>
    </div>
  );
}
