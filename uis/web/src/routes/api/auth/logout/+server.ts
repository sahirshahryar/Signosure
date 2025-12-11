import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { apiPost } from '$lib/server/api';

/**
 * POST /api/auth/logout
 *
 * Logs out the current user by deleting their session.
 * Proxies to the FastAPI core service and clears the local session cookie.
 */
export const POST: RequestHandler = async ({ cookies }) => {
    const sessionId = cookies.get('session_id');

    if (sessionId) {
        // Call FastAPI to delete the session from Redis
        await apiPost('/core/users/logout', {}, `session_id=${sessionId}`);
    }

    // Always clear the local cookie, even if the backend call failed
    cookies.delete('session_id', { path: '/' });

    return json({ success: true });
};
