/**
 * Server-side API client for communicating with the FastAPI core service.
 * This module should only be imported in +server.ts or +page.server.ts files.
 */

import { env } from '$env/dynamic/private';

// Default to localhost:8000 if not configured
const CORE_API_URL = env.CORE_API_URL ?? 'http://localhost:8000';

export interface ApiResponse<T = unknown, E = unknown> {
    ok: boolean;
    status: number;
    data?: T;
    error?: E;
    headers?: Headers;
}

/**
 * Makes a request to the FastAPI core service.
 * Handles form-urlencoded data (FastAPI's default for Form parameters).
 */
export async function apiRequest<T = unknown>(
    endpoint: string,
    options: {
        method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
        body?: Record<string, string | undefined>;
        cookies?: string;
    } = {}
): Promise<ApiResponse<T>> {
    const { method = 'GET', body, cookies } = options;

    const headers: Record<string, string> = {};

    // Forward cookies for session handling
    if (cookies) {
        headers['Cookie'] = cookies;
    }

    let fetchOptions: RequestInit = {
        method,
        headers
    };

    if (body && method !== 'GET') {
        // Filter out undefined values and encode as form data
        const formData = new URLSearchParams();
        for (const [key, value] of Object.entries(body)) {
            if (value !== undefined) {
                formData.append(key, value);
            }
        }
        headers['Content-Type'] = 'application/x-www-form-urlencoded';
        fetchOptions.body = formData.toString();
    }

    fetchOptions.headers = headers;

    try {
        const response = await fetch(`${CORE_API_URL}${endpoint}`, fetchOptions);

        // Try to parse JSON response
        let data: T | undefined;
        let error: unknown;

        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
            const json = await response.json();
            if (response.ok) {
                data = json as T;
            } else {
                // FastAPI returns { detail: ... } for errors
                // detail can be a string or an object like { valid: false, errors: [...] }
                error = json.detail ?? json;
            }
        } else if (!response.ok) {
            error = await response.text();
        }

        return {
            ok: response.ok,
            status: response.status,
            data,
            error,
            headers: response.headers
        };
    } catch (err) {
        return {
            ok: false,
            status: 0,
            error: err instanceof Error ? err.message : 'Unknown error occurred'
        };
    }
}

/**
 * Convenience wrapper for POST requests
 */
export function apiPost<T = unknown>(
    endpoint: string,
    body: Record<string, string | undefined>,
    cookies?: string
): Promise<ApiResponse<T>> {
    return apiRequest<T>(endpoint, { method: 'POST', body, cookies });
}

/**
 * Convenience wrapper for GET requests
 */
export function apiGet<T = unknown>(endpoint: string, cookies?: string): Promise<ApiResponse<T>> {
    return apiRequest<T>(endpoint, { method: 'GET', cookies });
}
