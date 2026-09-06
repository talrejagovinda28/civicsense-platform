const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
]);

export async function apiFetch<T>(
  path: string,
  token: string | null,
  options: RequestInit = {},
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers ?? {}),
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type HealthResponse = {
  status: string;
  database: string;
};

export type UserResponse = {
  user_id: string;
  role: string;
};

export type CategoryResponse = {
  id: string;
  name: string;
  slug: string;
};

export type SuggestCategoryResponse = {
  category_id: string;
  category_name: string;
  confidence: number;
};

export type CloudinarySignatureResponse = {
  cloud_name: string;
  api_key: string;
  timestamp: number;
  signature: string;
  folder: string;
};

export type ComplaintImageResponse = {
  id: string;
  cloudinary_url: string;
  sort_order: number;
};

export type ComplaintFeedItem = {
  id: string;
  title: string;
  description: string;
  status: string;
  category: CategoryResponse;
  ward: string | null;
  city: string;
  images: ComplaintImageResponse[];
  created_at: string;
};

export type PaginatedComplaints = {
  items: ComplaintFeedItem[];
  total: number;
  skip: number;
  limit: number;
};

export type StatusHistoryItem = {
  id: string;
  status: string;
  note: string | null;
  updated_by: string;
  created_at: string;
};

export type ComplaintDetail = ComplaintFeedItem & {
  updated_at: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  google_place_id?: string | null;
  user_id?: string | null;
  ai_suggested_category_id?: string | null;
  ai_confidence?: number | null;
  status_history?: StatusHistoryItem[];
};

export function validateImageFile(file: File): string | null {
  if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
    return "Only JPEG, PNG, and WebP images are allowed.";
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return "Each image must be 5 MB or smaller.";
  }
  return null;
}

export async function getCloudinarySignature(
  token: string,
): Promise<CloudinarySignatureResponse> {
  return apiFetch<CloudinarySignatureResponse>(
    "/api/v1/uploads/cloudinary-signature",
    token,
    { method: "POST" },
  );
}

export async function uploadToCloudinary(
  file: File,
  signature: CloudinarySignatureResponse,
): Promise<{ secure_url: string; public_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("api_key", signature.api_key);
  formData.append("timestamp", String(signature.timestamp));
  formData.append("signature", signature.signature);
  formData.append("folder", signature.folder);

  const response = await fetch(
    `https://api.cloudinary.com/v1_1/${signature.cloud_name}/image/upload`,
    { method: "POST", body: formData },
  );

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Cloudinary upload failed");
  }

  return response.json() as Promise<{ secure_url: string; public_id: string }>;
}

export type CreateComplaintPayload = {
  description: string;
  category_id: string;
  latitude: number;
  longitude: number;
  google_place_id: string;
  address: string;
  images: {
    cloudinary_url: string;
    cloudinary_public_id: string;
    sort_order: number;
  }[];
  title?: string;
  ward?: string | null;
  city?: string;
  ai_suggested_category_id?: string | null;
  ai_confidence?: number | null;
};

export async function createComplaint(
  token: string,
  payload: CreateComplaintPayload,
): Promise<ComplaintDetail> {
  return apiFetch<ComplaintDetail>("/api/v1/complaints", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getComplaint(
  token: string | null,
  complaintId: string,
): Promise<ComplaintDetail> {
  return apiFetch<ComplaintDetail>(`/api/v1/complaints/${complaintId}`, token);
}

export async function getOfficerQueue(token: string): Promise<ComplaintFeedItem[]> {
  return apiFetch<ComplaintFeedItem[]>("/api/v1/complaints/officer/queue", token);
}

export type StatusUpdatePayload = {
  status: string;
  note?: string | null;
};

export async function updateComplaintStatus(
  token: string,
  complaintId: string,
  payload: StatusUpdatePayload,
): Promise<ComplaintDetail> {
  return apiFetch<ComplaintDetail>(`/api/v1/complaints/${complaintId}/status`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  in_progress: "In Progress",
  resolved: "Resolved",
  closed: "Closed",
};

export function getNextStatusOptions(
  currentStatus: string,
  role: string,
): { value: string; label: string }[] {
  const options: Record<string, string[]> = {
    submitted: ["in_progress"],
    in_progress: ["resolved"],
    resolved: ["closed"],
    closed: [],
  };

  const next = [...(options[currentStatus] ?? [])];
  if (role === "admin" && currentStatus === "submitted") {
    next.push("closed");
  }

  return next.map((value) => ({
    value,
    label: STATUS_LABELS[value] ?? value,
  }));
}

export type AdminStats = {
  city: string;
  total: number;
  by_status: { label: string; count: number }[];
  by_category: { label: string; count: number }[];
};

export async function getAdminStats(token: string): Promise<AdminStats> {
  return apiFetch<AdminStats>("/api/v1/admin/stats", token);
}

export type RoleUpdatePayload = {
  role: "citizen" | "officer" | "admin";
};

export async function updateUserRole(
  token: string,
  userId: string,
  payload: RoleUpdatePayload,
): Promise<{ user_id: string; role: string }> {
  return apiFetch<{ user_id: string; role: string }>(
    `/api/v1/admin/users/${userId}/role`,
    token,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}
