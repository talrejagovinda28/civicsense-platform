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

export type CityResponse = {
  id: string;
  slug: string;
  name: string;
  state_name: string;
  state_code: string | null;
  country_code: string;
  status: "active" | "preview" | "disabled";
  municipality_name: string | null;
  center_lat: number;
  center_lng: number;
  default_zoom: number;
  supports_reporting: boolean;
  supports_ward_map: boolean;
  supports_accountability: boolean;
  map_data_version: string | null;
  created_at: string;
  updated_at: string;
};

export type ProvenanceInfo = {
  source_url: string | null;
  source_name: string | null;
  verified_at: string | null;
  notes: string | null;
};

export type OfficialSummary = {
  full_name: string;
  party: string | null;
  seat_label: string;
  reservation: string | null;
};

export type DepartmentSummary = {
  id: string;
  name: string;
  slug: string;
};

export type WardOfficeSummary = {
  id: string;
  name: string;
  slug: string;
};

export type ElectoralWardSummary = {
  id: string;
  ward_no: number;
  name: string;
};

export type RoutingChannelSummary = {
  id: string;
  channel_type: string;
  label: string;
  value: string;
  url: string | null;
  is_official: boolean;
  notes: string | null;
  provenance: ProvenanceInfo | null;
};

export type AccountabilityResponse = {
  city_slug: string;
  municipality_name: string;
  inside_supported_area: boolean;
  electoral_ward: ElectoralWardSummary | null;
  ward_office: WardOfficeSummary | null;
  department: DepartmentSummary | null;
  elected_representatives: OfficialSummary[];
  routing_channels: RoutingChannelSummary[];
  warnings: string[];
  provenance: ProvenanceInfo | null;
};

export type ExternalSubmissionResponse = {
  id: string;
  complaint_id: string;
  routing_channel_id: string | null;
  provider: string;
  status: string;
  external_token: string | null;
  status_url: string | null;
  forwarded_at: string | null;
  token_received_at: string | null;
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
  public_latitude: number | null;
  public_longitude: number | null;
  electoral_ward_id: string | null;
  category_id: string | null;
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
  department_id?: string | null;
  ward_office_id?: string | null;
  city_id?: string | null;
  external_submission?: ExternalSubmissionResponse | null;
  approximate_location_label?: string | null;
};

export type ComplaintFilters = {
  city?: string;
  electoral_ward_id?: string;
  status?: string;
  category_id?: string;
  skip?: number;
  limit?: number;
};

function buildQueryString(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function getCities(): Promise<CityResponse[]> {
  return apiFetch<CityResponse[]>("/api/v1/cities", null);
}

export async function getCity(slug: string): Promise<CityResponse> {
  return apiFetch<CityResponse>(`/api/v1/cities/${slug}`, null);
}

export async function getCityWards(slug: string): Promise<ElectoralWardSummary[]> {
  return apiFetch<ElectoralWardSummary[]>(`/api/v1/cities/${slug}/wards`, null);
}

export type WardGeoJson = {
  type: "FeatureCollection";
  features: object[];
};

export async function getWardGeoJson(slug: string): Promise<WardGeoJson> {
  const response = await fetch(`${API_URL}/api/v1/cities/${slug}/wards/geojson`);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<WardGeoJson>;
}

export async function getAccountability(
  citySlug: string,
  lat: number,
  lng: number,
  categoryId: string,
): Promise<AccountabilityResponse> {
  const query = buildQueryString({ lat, lng, category_id: categoryId });
  return apiFetch<AccountabilityResponse>(
    `/api/v1/cities/${citySlug}/accountability${query}`,
    null,
  );
}

export async function getComplaints(
  filters: ComplaintFilters = {},
): Promise<PaginatedComplaints> {
  const query = buildQueryString({
    city: filters.city,
    electoral_ward_id: filters.electoral_ward_id,
    status: filters.status,
    category_id: filters.category_id,
    skip: filters.skip,
    limit: filters.limit,
  });
  return apiFetch<PaginatedComplaints>(`/api/v1/complaints${query}`, null);
}

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
  latitude: number | null;
  longitude: number | null;
  google_place_id: string | null;
  address: string;
  images: {
    cloudinary_url: string;
    cloudinary_public_id: string;
    sort_order: number;
  }[];
  title?: string;
  ward?: string | null;
  city?: string;
  city_slug?: string;
  ai_suggested_category_id?: string | null;
  ai_confidence?: number | null;
};

export type ExternalSubmissionStartPayload = {
  routing_channel_id?: string | null;
};

export type ExternalSubmissionTokenPayload = {
  external_token: string;
  status_url?: string | null;
};

export async function startExternalSubmission(
  token: string,
  complaintId: string,
  payload: ExternalSubmissionStartPayload = {},
): Promise<ExternalSubmissionResponse> {
  return apiFetch<ExternalSubmissionResponse>(
    `/api/v1/complaints/${complaintId}/external-submission/start`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function saveExternalSubmissionToken(
  token: string,
  complaintId: string,
  payload: ExternalSubmissionTokenPayload,
): Promise<ExternalSubmissionResponse> {
  return apiFetch<ExternalSubmissionResponse>(
    `/api/v1/complaints/${complaintId}/external-submission/token`,
    token,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

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

export async function getOfficerQueue(
  token: string,
  city?: string,
): Promise<ComplaintFeedItem[]> {
  const query = city ? buildQueryString({ city }) : "";
  return apiFetch<ComplaintFeedItem[]>(
    `/api/v1/complaints/officer/queue${query}`,
    token,
  );
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

export const STATUS_COLORS: Record<string, string> = {
  submitted: "#2563eb",
  in_progress: "#d97706",
  resolved: "#16a34a",
  closed: "#64748b",
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
