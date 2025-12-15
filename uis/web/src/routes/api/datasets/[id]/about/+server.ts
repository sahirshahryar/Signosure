import { apiGet } from '$lib/server/api';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export interface PromptData {
    id: string;
    internal_name: string;
    display_text: string;
    reference_type: string;
}

export interface DatasetContentsInfo {
    id: string;
    summary: Record<string, unknown> | null;
    summary_updated: number | null;
    stale: boolean;
}

export interface DatasetDetails {
    id: string;
    name: string;
    language: string;
    region: string;
    scope: {
        id: string;
        name: string;
    };
    default_repetitions: number;
    prompts_assigned: number;
    sequential_unique_prompts: boolean;
    collector_code: string;
    collector_reg_open: boolean;
    collector_req_approval: boolean;
    annotator_code: string;
    annotator_reg_open: boolean;
    annotator_req_approval: boolean;
    prompt_data: PromptData[];
    review_classifications: string[];
    device_bans: string[];
    contents: DatasetContentsInfo;
    can_edit: boolean;
}

export const GET: RequestHandler = async ({ params, cookies }) => {
    const { id } = params;

    const cookieHeader = cookies.get('session_id')
        ? `session_id=${cookies.get('session_id')}`
        : '';

    const response = await apiGet<DatasetDetails>(
        `/core/datasets/about/${id}`,
        cookieHeader
    );

    if (!response.ok) {
        return json(
            { error: response.error || 'Failed to fetch dataset' },
            { status: response.status || 500 }
        );
    }

    return json(response.data);
};
