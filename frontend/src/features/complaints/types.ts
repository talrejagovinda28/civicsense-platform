export type ComplaintImageDraft = {
  cloudinaryUrl: string;
  cloudinaryPublicId: string;
  sortOrder: number;
};

export type ComplaintDraft = {
  latitude: number | null;
  longitude: number | null;
  googlePlaceId: string | null;
  address: string | null;
  ward: string | null;
  city: string;
  images: ComplaintImageDraft[];
  categoryId: string | null;
  categoryName: string | null;
  aiSuggestedCategoryId: string | null;
  aiConfidence: number | null;
  title: string;
  description: string;
};

export const COMPLAINT_WIZARD_STEPS = [
  "location",
  "photo",
  "category",
  "description",
  "review",
] as const;

export type ComplaintWizardStep = (typeof COMPLAINT_WIZARD_STEPS)[number];

export const emptyComplaintDraft = (): ComplaintDraft => ({
  latitude: null,
  longitude: null,
  googlePlaceId: null,
  address: null,
  ward: null,
  city: "Pune",
  images: [],
  categoryId: null,
  categoryName: null,
  aiSuggestedCategoryId: null,
  aiConfidence: null,
  title: "",
  description: "",
});
