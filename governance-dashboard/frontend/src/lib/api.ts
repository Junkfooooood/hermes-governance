import { ApiError, type ApiResponse, type ApiErrorResponse } from "./types";

/**
 * Unified fetch wrapper that unwraps {data, meta} responses.
 * Throws ApiError on non-2xx responses.
 */
export async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  const body = await res.json();

  if (!res.ok) {
    const errBody = body as ApiErrorResponse;
    throw new ApiError(
      errBody.error ?? { code: "UNKNOWN", message: res.statusText }
    );
  }

  const wrapped = body as ApiResponse<T>;
  return wrapped.data;
}

/**
 * POST request with JSON body, returns unwrapped data.
 */
export async function postJSON<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();

  if (!res.ok) {
    const errBody = data as ApiErrorResponse;
    throw new ApiError(
      errBody.error ?? { code: "UNKNOWN", message: res.statusText }
    );
  }

  const wrapped = data as ApiResponse<T>;
  return wrapped.data;
}

/**
 * PATCH request with JSON body, returns unwrapped data.
 */
export async function patchJSON<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();

  if (!res.ok) {
    const errBody = data as ApiErrorResponse;
    throw new ApiError(
      errBody.error ?? { code: "UNKNOWN", message: res.statusText }
    );
  }

  const wrapped = data as ApiResponse<T>;
  return wrapped.data;
}
