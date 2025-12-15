import { apiGet } from '$lib/server/api';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export interface DatasetSummaryResponse {
    contents: string;
    summary: Record<string, unknown> | null;
    summary_updated: number | null;
    stale: boolean;
}

export const GET: RequestHandler = async ({ params, cookies }) => {
    const { id } = params;

    const cookieHeader = cookies.get('session_id')
        ? `session_id=${cookies.get('session_id')}`
        : '';

    const response = await apiGet<DatasetSummaryResponse>(
        `/core/datasets/summarize/${id}`,
        cookieHeader
    );

    if (!response.ok) {
        return json(
            { error: response.error || 'Failed to refresh summary' },
            { status: response.status || 500 }
        );
    }

    return json(response.data);
};
