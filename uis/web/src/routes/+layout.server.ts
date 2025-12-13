import { apiGet } from '$lib/server/api';
import type { LayoutServerLoad } from './$types';

export interface UserInfo {
    id: string;
    email: string;
    name: string | null;
    validated: boolean;
    admin: boolean;
}

export const load: LayoutServerLoad = async ({ cookies }) => {
    const cookieHeader = cookies.get('session_id')
        ? `session_id=${cookies.get('session_id')}`
        : undefined;

    if (!cookieHeader) {
        return { user: null };
    }

    const response = await apiGet<UserInfo>('/core/users/me', cookieHeader);

    if (response.ok && response.data) {
        return { user: response.data };
    }

    return { user: null };
};
