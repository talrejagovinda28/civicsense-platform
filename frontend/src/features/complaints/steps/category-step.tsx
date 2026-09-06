"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import {
  apiFetch,
  CategoryResponse,
  SuggestCategoryResponse,
} from "@/lib/api";

import { useComplaintWizard } from "../wizard-context";

export function CategoryStep() {
  const { getToken } = useAuth();
  const { draft, updateDraft } = useComplaintWizard();
  const [suggestError, setSuggestError] = useState<string | null>(null);

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => apiFetch<CategoryResponse[]>("/api/v1/categories", null),
  });

  useEffect(() => {
    if (draft.images.length === 0 || draft.aiSuggestedCategoryId) {
      return;
    }

    const loadSuggestion = async () => {
      try {
        const token = await getToken();
        if (!token) {
          return;
        }

        const suggestion = await apiFetch<SuggestCategoryResponse>(
          "/api/v1/complaints/suggest-category",
          token,
          {
            method: "POST",
            body: JSON.stringify({
              photo_urls: draft.images.map((image) => image.cloudinaryUrl),
            }),
          },
        );

        updateDraft({
          aiSuggestedCategoryId: suggestion.category_id,
          aiConfidence: suggestion.confidence,
          categoryId: suggestion.category_id,
          categoryName: suggestion.category_name,
        });
      } catch (error) {
        setSuggestError(
          error instanceof Error
            ? error.message
            : "Could not load AI category suggestion.",
        );
      }
    };

    void loadSuggestion();
  }, [
    draft.aiSuggestedCategoryId,
    draft.images,
    getToken,
    updateDraft,
  ]);

  if (categoriesQuery.isLoading) {
    return <p className="text-sm text-neutral-500">Loading categories…</p>;
  }

  if (categoriesQuery.error) {
    return (
      <p className="text-sm text-red-600">
        Could not load categories. Check that the API and database are running.
      </p>
    );
  }

  const categories = categoriesQuery.data ?? [];

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        We suggested a category based on your photo. You can change it if needed.
      </p>

      {draft.aiSuggestedCategoryId && draft.aiConfidence !== null && (
        <div className="rounded-lg bg-neutral-50 px-4 py-3 text-sm">
          Suggested:{" "}
          <span className="font-medium">{draft.categoryName ?? "Category"}</span>{" "}
          ({Math.round(draft.aiConfidence * 100)}%)
        </div>
      )}

      {suggestError && (
        <p className="text-sm text-amber-700">
          AI suggestion unavailable — please pick a category manually.
        </p>
      )}

      <div className="grid gap-2 sm:grid-cols-2">
        {categories.map((category) => {
          const selected = draft.categoryId === category.id;

          return (
            <button
              key={category.id}
              type="button"
              onClick={() =>
                updateDraft({
                  categoryId: category.id,
                  categoryName: category.name,
                })
              }
              className={`rounded-lg border px-4 py-3 text-left text-sm font-medium ${
                selected
                  ? "border-neutral-900 bg-neutral-900 text-white"
                  : "border-neutral-300 hover:border-neutral-500"
              }`}
            >
              {category.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
