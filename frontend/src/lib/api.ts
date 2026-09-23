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
  verification_state?: string | null;
  is_sensitive?: boolean;
  anonymous_to_public?: boolean;
  viewer_is_owner?: boolean;
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
  anonymous_to_public?: boolean;
  is_sensitive?: boolean;
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

// --- Social / feed / messaging (graceful when backend not yet deployed) ---

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; unavailable: boolean; error: string };

export async function apiFetchOptional<T>(
  path: string,
  token: string | null,
  options: RequestInit = {},
): Promise<ApiResult<T>> {
  try {
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

    if (response.status === 404) {
      return { ok: false, unavailable: true, error: "Endpoint not available" };
    }

    if (!response.ok) {
      const message = await response.text();
      return {
        ok: false,
        unavailable: false,
        error: message || `Request failed: ${response.status}`,
      };
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return { ok: true, data: null as T };
    }

    const text = await response.text();
    if (!text) {
      return { ok: true, data: null as T };
    }

    return { ok: true, data: JSON.parse(text) as T };
  } catch (error) {
    return {
      ok: false,
      unavailable: false,
      error: error instanceof Error ? error.message : "Network error",
    };
  }
}

export type FeedItemKind = "complaint" | "update";

export type FeedItem = {
  id: string;
  kind: FeedItemKind;
  complaint_id: string;
  title: string;
  description?: string | null;
  status: string;
  category_name?: string | null;
  locality_label?: string | null;
  responsibility_line?: string | null;
  image_url?: string | null;
  images?: ComplaintImageResponse[];
  like_count: number;
  affected_count: number;
  comment_count: number;
  viewer_liked?: boolean;
  viewer_affected?: boolean;
  created_at: string;
};

export type FeedResponse = {
  items: FeedItem[];
  next_cursor: string | null;
};

export type EngagementCounts = {
  like_count: number;
  affected_count: number;
  comment_count: number;
  viewer_liked: boolean;
  viewer_affected: boolean;
};

export type CommentItem = {
  id: string;
  complaint_id: string;
  author_handle: string;
  author_display_name: string;
  body: string;
  is_official: boolean;
  created_at: string;
};

export type PaginatedComments = {
  items: CommentItem[];
  total: number;
  skip: number;
  limit: number;
};

export type ProfileResponse = {
  id: string;
  handle: string;
  display_name: string;
  bio: string | null;
  is_private: boolean;
  follower_count: number;
  following_count: number;
  viewer_is_following: boolean;
  viewer_follow_pending: boolean;
  messaging_user_id?: string | null;
};

export type FollowResponse = {
  id: string;
  follower_id: string;
  target_id: string;
  status: string;
  created_at: string;
};

export type PendingFollowRequest = {
  id: string;
  follower_id: string;
  follower_handle: string;
  follower_display_name: string;
  created_at: string;
};

export type OwnProfileResponse = ProfileResponse & {
  home_locality: string | null;
};

export type ReputationResponse = {
  lifetime_xp: number;
  eligible_xp: number;
  badges: { code: string; label: string; granted_at: string }[];
  unlocks: {
    can_initiate_dm: boolean;
    can_create_groups: boolean;
  };
};

export type ChatSummary = {
  id: string;
  title: string;
  kind: "direct" | "group" | "issue";
  last_message_preview: string | null;
  last_message_at: string | null;
  unread_count: number;
};

export type ChatMessage = {
  id: string;
  chat_id: string;
  sender_handle: string;
  sender_display_name: string;
  body: string;
  created_at: string;
};

export type PaginatedMessages = {
  items: ChatMessage[];
  next_cursor: string | null;
};

function complaintToFeedItem(
  complaint: ComplaintFeedItem,
  token: string | null = null,
): FeedItem {
  void token;
  return {
    id: complaint.id,
    kind: "complaint",
    complaint_id: complaint.id,
    title: complaint.title,
    description: complaint.description,
    status: complaint.status,
    category_name: complaint.category.name,
    locality_label: complaint.ward ?? complaint.city,
    responsibility_line: "Responsibility being verified",
    image_url: complaint.images[0]?.cloudinary_url ?? null,
    images: complaint.images,
    like_count: 0,
    affected_count: 0,
    comment_count: 0,
    created_at: complaint.created_at,
  };
}

export async function getFeed(
  citySlug: string,
  token: string | null = null,
  cursor?: string,
): Promise<FeedResponse & { fallback?: boolean }> {
  const query = buildQueryString({
    city: citySlug,
    mode: "blend",
    cursor,
  });

  const result = await apiFetchOptional<FeedResponse>(`/api/v1/feed${query}`, token);

  if (result.ok) {
    return result.data;
  }

  const complaints = await getComplaints({ city: citySlug, limit: 50 });
  return {
    items: complaints.items.map((item) => complaintToFeedItem(item, token)),
    next_cursor: null,
    fallback: true,
  };
}

export async function getComplaintEngagement(
  token: string | null,
  complaintId: string,
): Promise<EngagementCounts | null> {
  const result = await apiFetchOptional<EngagementCounts>(
    `/api/v1/complaints/${complaintId}/engagement`,
    token,
  );
  return result.ok ? result.data : null;
}

export async function likeComplaint(
  token: string,
  complaintId: string,
): Promise<ApiResult<EngagementCounts>> {
  return apiFetchOptional<EngagementCounts>(
    `/api/v1/complaints/${complaintId}/like`,
    token,
    { method: "PUT" },
  );
}

export async function unlikeComplaint(
  token: string,
  complaintId: string,
): Promise<ApiResult<EngagementCounts>> {
  return apiFetchOptional<EngagementCounts>(
    `/api/v1/complaints/${complaintId}/like`,
    token,
    { method: "DELETE" },
  );
}

export async function markAffected(
  token: string,
  complaintId: string,
): Promise<ApiResult<EngagementCounts>> {
  return apiFetchOptional<EngagementCounts>(
    `/api/v1/complaints/${complaintId}/affected`,
    token,
    { method: "PUT" },
  );
}

export async function unmarkAffected(
  token: string,
  complaintId: string,
): Promise<ApiResult<EngagementCounts>> {
  return apiFetchOptional<EngagementCounts>(
    `/api/v1/complaints/${complaintId}/affected`,
    token,
    { method: "DELETE" },
  );
}

export async function getComments(
  complaintId: string,
  skip = 0,
  limit = 30,
): Promise<PaginatedComments | null> {
  const query = buildQueryString({ skip, limit });
  const result = await apiFetchOptional<PaginatedComments>(
    `/api/v1/complaints/${complaintId}/comments${query}`,
    null,
  );
  return result.ok ? result.data : null;
}

export async function postComment(
  token: string,
  complaintId: string,
  body: string,
): Promise<ApiResult<CommentItem>> {
  return apiFetchOptional<CommentItem>(
    `/api/v1/complaints/${complaintId}/comments`,
    token,
    { method: "POST", body: JSON.stringify({ body }) },
  );
}

export async function getOwnProfile(token: string): Promise<OwnProfileResponse | null> {
  const result = await apiFetchOptional<OwnProfileResponse>(
    "/api/v1/profiles/me",
    token,
  );
  return result.ok ? result.data : null;
}

export async function updateOwnProfile(
  token: string,
  payload: { is_private?: boolean; display_name?: string; bio?: string },
): Promise<ApiResult<OwnProfileResponse>> {
  return apiFetchOptional<OwnProfileResponse>("/api/v1/profiles/me", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getPublicProfile(
  handle: string,
  token: string | null = null,
): Promise<ProfileResponse | null> {
  const result = await apiFetchOptional<ProfileResponse>(
    `/api/v1/profiles/${encodeURIComponent(handle)}`,
    token,
  );
  return result.ok ? result.data : null;
}

export async function getReputation(token: string): Promise<ReputationResponse | null> {
  const result = await apiFetchOptional<ReputationResponse>(
    "/api/v1/profiles/me/reputation",
    token,
  );
  return result.ok ? result.data : null;
}

export async function followProfile(
  token: string,
  profileId: string,
): Promise<ApiResult<FollowResponse>> {
  return apiFetchOptional<FollowResponse>(
    `/api/v1/profiles/${profileId}/follow`,
    token,
    { method: "POST" },
  );
}

export async function unfollowProfile(
  token: string,
  profileId: string,
): Promise<ApiResult<null>> {
  return apiFetchOptional<null>(
    `/api/v1/profiles/${profileId}/follow`,
    token,
    { method: "DELETE" },
  );
}

export async function decideFollowRequest(
  token: string,
  followId: string,
  accept: boolean,
): Promise<ApiResult<FollowResponse>> {
  return apiFetchOptional<FollowResponse>(
    `/api/v1/follow-requests/${followId}/decide`,
    token,
    { method: "POST", body: JSON.stringify({ accept }) },
  );
}

export async function getPendingFollowRequests(
  token: string,
): Promise<PendingFollowRequest[]> {
  const result = await apiFetchOptional<PendingFollowRequest[]>(
    "/api/v1/profiles/me/follow-requests",
    token,
  );
  return result.ok && result.data ? result.data : [];
}

// --- Submissions (V3) ---

export type ConsentResponse = {
  id: string;
  complaint_id: string;
  channel_id: string;
  payload_hash: string;
  authorized_at: string;
};

export type DispatchResponse = {
  intent_id?: string | null;
  status: string;
  outcome_state?: string | null;
  message?: string | null;
  provider_message_id?: string | null;
  official_reference?: string | null;
  metadata?: Record<string, unknown> | null;
  unknown_outcome?: boolean | null;
  attempt_no?: number | null;
  idempotent_replay?: boolean | null;
  code?: string | null;
};

export type IntentResponse = {
  id: string;
  complaint_id: string;
  status: string;
  idempotency_key: string;
  created_at: string;
};

export type ExternalReferenceResponse = {
  id: string;
  reference_value: string;
  reference_type: string;
  tracking_url: string | null;
  created_at: string;
};

export type SubmissionChannelSummary = {
  id: string;
  label: string;
  channel_type: string;
  mode: string;
  enabled: boolean;
  url?: string | null;
};

export async function createSubmissionConsent(
  token: string,
  complaintId: string,
  payload: {
    channel_id: string;
    disclosure_json: Record<string, unknown>;
    scope?: string;
  },
): Promise<ApiResult<ConsentResponse>> {
  return apiFetchOptional<ConsentResponse>(
    `/api/v1/complaints/${complaintId}/authorization`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function dispatchSubmission(
  token: string,
  complaintId: string,
  payload: { consent_id: string; idempotency_key: string },
): Promise<ApiResult<DispatchResponse>> {
  return apiFetchOptional<DispatchResponse>(
    `/api/v1/complaints/${complaintId}/submissions`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function attestSubmissionSent(
  token: string,
  intentId: string,
  note?: string,
): Promise<ApiResult<IntentResponse>> {
  return apiFetchOptional<IntentResponse>(
    `/api/v1/submissions/${intentId}/attest-sent`,
    token,
    {
      method: "POST",
      body: JSON.stringify({ attestation_note: note ?? null }),
    },
  );
}

export async function attachSubmissionReference(
  token: string,
  intentId: string,
  payload: { reference_value: string; tracking_url?: string | null },
): Promise<ApiResult<ExternalReferenceResponse>> {
  return apiFetchOptional<ExternalReferenceResponse>(
    `/api/v1/submissions/${intentId}/reference`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function getComplaintSubmissionChannels(
  token: string | null,
  complaintId: string,
): Promise<SubmissionChannelSummary[]> {
  const result = await apiFetchOptional<SubmissionChannelSummary[]>(
    `/api/v1/complaints/${complaintId}/submission-channels`,
    token,
  );
  return result.ok && result.data ? result.data : [];
}

// --- Timeline ---

export type TimelineEvent = {
  id: string;
  event_type: string;
  actor_kind: string;
  public_payload?: Record<string, unknown> | null;
  created_at: string;
};

export type ComplaintTimelineResponse = {
  items: TimelineEvent[];
};

export async function getComplaintTimeline(
  token: string | null,
  complaintId: string,
): Promise<ComplaintTimelineResponse | null> {
  const result = await apiFetchOptional<ComplaintTimelineResponse>(
    `/api/v1/complaints/${complaintId}/timeline`,
    token,
  );
  return result.ok ? result.data : null;
}

// --- Resolution ---

export type EvidenceResponse = {
  id: string;
  complaint_id: string;
  submitter_id: string;
  submitter_role: string;
  assertion: string;
  status: string;
  created_at: string;
};

export type VerificationResponse = {
  id: string;
  verification_state: string;
};

export type ReviewResponse = {
  id: string;
  complaint_id: string;
  evidence_id: string | null;
  decision: string;
  reviewer_id: string;
  created_at: string;
};

export async function submitResolutionEvidence(
  token: string,
  complaintId: string,
  payload: { assertion: string; media_url?: string | null },
): Promise<ApiResult<EvidenceResponse>> {
  return apiFetchOptional<EvidenceResponse>(
    `/api/v1/complaints/${complaintId}/resolution-evidence`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function confirmResolution(
  token: string,
  complaintId: string,
  payload: { confirmed: boolean; reason?: string | null },
): Promise<ApiResult<VerificationResponse>> {
  return apiFetchOptional<VerificationResponse>(
    `/api/v1/complaints/${complaintId}/resolution-confirmation`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export async function reviewResolution(
  token: string,
  complaintId: string,
  payload: {
    evidence_id?: string | null;
    decision: string;
    reason?: string | null;
  },
): Promise<ApiResult<ReviewResponse>> {
  return apiFetchOptional<ReviewResponse>(
    `/api/v1/complaints/${complaintId}/resolution-review`,
    token,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export const VERIFICATION_STATE_LABELS: Record<string, string> = {
  none: "Not verified",
  pending: "Pending verification",
  confirmed_by_reporter: "Confirmed by reporter",
  verified: "Independently verified",
  disputed: "Disputed",
};

// --- Messaging (extended) ---

export type DirectChatResponse = {
  type: string;
  conversation_id?: string | null;
  request_id?: string | null;
  status?: string | null;
};

export type ConversationResponse = {
  id: string;
  type: string;
  name: string | null;
  created_by: string;
  visibility: string;
  created_at: string;
};

export async function createDirectChat(
  token: string,
  recipientClerkUserId: string,
): Promise<ApiResult<DirectChatResponse>> {
  return apiFetchOptional<DirectChatResponse>("/api/v1/chats/direct", token, {
    method: "POST",
    body: JSON.stringify({ recipient_id: recipientClerkUserId }),
  });
}

export async function createGroupChat(
  token: string,
  payload: { name: string; type?: string },
): Promise<ApiResult<ConversationResponse>> {
  return apiFetchOptional<ConversationResponse>("/api/v1/chats/groups", token, {
    method: "POST",
    body: JSON.stringify({
      name: payload.name,
      visibility: payload.type ?? "private",
    }),
  });
}

export async function decideChatRequest(
  token: string,
  requestId: string,
  decision: "accept" | "decline" | "block",
): Promise<ApiResult<Record<string, unknown>>> {
  return apiFetchOptional<Record<string, unknown>>(
    `/api/v1/chats/requests/${requestId}/decide`,
    token,
    { method: "POST", body: JSON.stringify({ decision }) },
  );
}

export async function getChats(token: string): Promise<ChatSummary[]> {
  const result = await apiFetchOptional<ChatSummary[]>("/api/v1/chats", token);
  return result.ok ? result.data : [];
}

export async function getChatMessages(
  token: string,
  chatId: string,
  cursor?: string,
): Promise<PaginatedMessages | null> {
  const query = buildQueryString({ cursor });
  const result = await apiFetchOptional<PaginatedMessages>(
    `/api/v1/chats/${chatId}/messages${query}`,
    token,
  );
  return result.ok ? result.data : null;
}

export async function sendChatMessage(
  token: string,
  chatId: string,
  body: string,
): Promise<ApiResult<ChatMessage>> {
  return apiFetchOptional<ChatMessage>(`/api/v1/chats/${chatId}/messages`, token, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}
