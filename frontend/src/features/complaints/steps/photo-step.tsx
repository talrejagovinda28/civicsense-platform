"use client";

import { useAuth } from "@clerk/nextjs";
import { useRef, useState } from "react";

import {
  getCloudinarySignature,
  uploadToCloudinary,
  validateImageFile,
} from "@/lib/api";

import { useComplaintWizard } from "../wizard-context";

export function PhotoStep() {
  const { getToken } = useAuth();
  const { draft, updateDraft } = useComplaintWizard();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const removePhoto = (index: number) => {
    updateDraft({
      images: draft.images
        .filter((_, itemIndex) => itemIndex !== index)
        .map((image, itemIndex) => ({ ...image, sortOrder: itemIndex })),
    });
  };

  const handleFilesSelected = async (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const remainingSlots = 3 - draft.images.length;
    if (remainingSlots <= 0) {
      setError("You can attach up to 3 photos.");
      return;
    }

    const selectedFiles = Array.from(files).slice(0, remainingSlots);
    for (const file of selectedFiles) {
      const validationError = validateImageFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    setUploading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("You must be signed in to upload photos.");
      }

      const signature = await getCloudinarySignature(token);
      const uploadedImages = [];

      for (const [index, file] of selectedFiles.entries()) {
        const result = await uploadToCloudinary(file, signature);
        uploadedImages.push({
          cloudinaryUrl: result.secure_url,
          cloudinaryPublicId: result.public_id,
          sortOrder: draft.images.length + index,
        });
      }

      updateDraft({ images: [...draft.images, ...uploadedImages] });
    } catch (uploadError) {
      const message =
        uploadError instanceof Error
          ? uploadError.message
          : "Photo upload failed.";
      setError(message);
    } finally {
      setUploading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Add 1–3 photos of the issue. JPEG, PNG, or WebP up to 5 MB each.
      </p>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        multiple
        disabled={uploading || draft.images.length >= 3}
        onChange={(event) => handleFilesSelected(event.target.files)}
        className="block w-full text-sm text-neutral-600 file:mr-4 file:rounded-lg file:border-0 file:bg-neutral-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-neutral-800"
      />

      {uploading && (
        <p className="text-sm text-neutral-500">Uploading to Cloudinary…</p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {draft.images.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-3">
          {draft.images.map((image, index) => (
            <li
              key={image.cloudinaryPublicId}
              className="overflow-hidden rounded-lg border border-neutral-200"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={image.cloudinaryUrl}
                alt={`Complaint photo ${index + 1}`}
                className="h-32 w-full object-cover"
              />
              <div className="flex items-center justify-between px-3 py-2">
                <span className="text-xs text-neutral-500">Photo {index + 1}</span>
                <button
                  type="button"
                  onClick={() => removePhoto(index)}
                  className="text-xs text-red-600 hover:underline"
                >
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <p className="text-xs text-neutral-500">
        {draft.images.length}/3 photos attached
      </p>
    </div>
  );
}
