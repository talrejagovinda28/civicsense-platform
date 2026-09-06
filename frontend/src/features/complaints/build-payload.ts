import type { ComplaintDraft } from "./types";
import type { CreateComplaintPayload } from "@/lib/api";

export function buildCreateComplaintPayload(
  draft: ComplaintDraft,
): CreateComplaintPayload {
  if (
    draft.latitude === null ||
    draft.longitude === null ||
    !draft.googlePlaceId ||
    !draft.address ||
    !draft.categoryId
  ) {
    throw new Error("Complaint draft is incomplete");
  }

  return {
    description: draft.description.trim(),
    category_id: draft.categoryId,
    latitude: draft.latitude,
    longitude: draft.longitude,
    google_place_id: draft.googlePlaceId,
    address: draft.address,
    ward: draft.ward,
    city: draft.city,
    ai_suggested_category_id: draft.aiSuggestedCategoryId,
    ai_confidence: draft.aiConfidence,
    images: draft.images.map((image) => ({
      cloudinary_url: image.cloudinaryUrl,
      cloudinary_public_id: image.cloudinaryPublicId,
      sort_order: image.sortOrder,
    })),
  };
}
