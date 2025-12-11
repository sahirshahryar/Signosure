import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { apiPost } from '$lib/server/api';

interface ValidateResponse {
    valid: boolean;
}

interface CreateUserResponse {
    success: boolean;
    user_id: string;
    message: string;
}

/**
 * POST /api/auth/signup
 *
 * Validates and creates a new user account.
 * Proxies to the FastAPI core service.
 */
export const POST: RequestHandler = async ({ request }) => {
    const formData = await request.formData();

    const email = formData.get('email')?.toString();
    const password = formData.get('password')?.toString();
    const registrationCode = formData.get('registration_code')?.toString();

    // Basic validation
    if (!email || !password) {
        return json({ error: 'Email and password are required' }, { status: 400 });
    }

    // First validate the user data
    const validateResult = await apiPost<ValidateResponse>('/core/users/validate', {
        email,
        password,
        registration_code: registrationCode
    });

    if (!validateResult.ok) {
        return json(
            { error: validateResult.error ?? 'Validation failed' },
            { status: validateResult.status || 400 }
        );
    }

    // Create the user
    const createResult = await apiPost<CreateUserResponse>('/core/users/create', {
        email,
        password,
        registration_code: registrationCode
    });

    if (!createResult.ok) {
        return json(
            { error: createResult.error ?? 'Failed to create account' },
            { status: createResult.status || 500 }
        );
    }

    return json({
        success: true,
        message: createResult.data?.message ?? 'Account created successfully'
    });
};
