import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { apiPost } from '$lib/server/api';

interface LoginResponse {
    success: boolean;
    user_id: string;
    validated: boolean;
}

/**
 * POST /api/auth/login
 *
 * Authenticates a user and establishes a session.
 * Proxies to the FastAPI core service and forwards the session cookie.
 */
export const POST: RequestHandler = async ({ request, cookies }) => {
    const formData = await request.formData();

    const email = formData.get('email')?.toString();
    const password = formData.get('password')?.toString();

    if (!email || !password) {
        return json({ error: 'Email and password are required' }, { status: 400 });
    }

    const result = await apiPost<LoginResponse>('/core/users/login', {
        email,
        password
    });

    if (!result.ok) {
        return json({ error: result.error ?? 'Login failed' }, { status: result.status || 401 });
    }

    // Forward the session cookie from FastAPI to the browser
    const setCookie = result.headers?.get('set-cookie');
    if (setCookie) {
        // Parse the Set-Cookie header from FastAPI
        // Format: session_id=value; Max-Age=...; Path=/; HttpOnly; Secure; SameSite=lax
        const cookieMatch = setCookie.match(/session_id=([^;]+)/);
        if (cookieMatch) {
            cookies.set('session_id', cookieMatch[1], {
                path: '/',
                httpOnly: true,
                secure: true,
                sameSite: 'lax',
                maxAge: 7 * 24 * 60 * 60 // 7 days
            });
        }
    }

    return json({
        success: true,
        validated: result.data?.validated ?? false
    });
};
