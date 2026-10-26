import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, parent }) => {
    const { user } = await parent();

    if (!user) {
        throw redirect(303, '/auth/login');
    }

    // TODO: load annotation dashboard data
    return {};
};
