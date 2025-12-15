import { apiGet } from '$lib/server/api';
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export interface DatasetSummary {
    id: string;
    name: string;
    language: string;
    region: string | null;
    can_edit: boolean;
}

export const load: PageServerLoad = async ({ cookies, parent }) => {
    const { user } = await parent();

    if (!user) {
        throw redirect(303, '/auth/login');
    }

    const cookieHeader = `session_id=${cookies.get('session_id')}`;

    const response = await apiGet<DatasetSummary[]>('/core/datasets/list', cookieHeader);

    if (response.ok && response.data) {
        return { datasets: response.data };
    }

    return { datasets: [] };
};
