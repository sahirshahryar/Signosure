import { apiPost } from '$lib/server/api';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

interface CreateDatasetResponse {
    success: boolean;
    id: string;
}

export const POST: RequestHandler = async ({ request, cookies }) => {
    const formData = await request.formData();

    const name = formData.get('name')?.toString();
    const language = formData.get('language')?.toString();
    const region = formData.get('region')?.toString();
    const defaultReps = formData.get('default_reps')?.toString();
    const promptsPerUser = formData.get('prompts_per_user')?.toString();
    const sequentialUniquePrompts = formData.get('sequential_unique_prompts')?.toString();
    const collectorOpenRegistration = formData.get('collector_open_registration')?.toString();
    const collectorsRequireApproval = formData.get('collectors_require_approval')?.toString();
    const annotatorOpenRegistration = formData.get('annotator_open_registration')?.toString();
    const annotatorsRequireApproval = formData.get('annotators_require_approval')?.toString();

    if (!name || !language) {
        return json({ error: 'Name and language are required' }, { status: 400 });
    }

    const cookieHeader = cookies.get('session_id')
        ? `session_id=${cookies.get('session_id')}`
        : '';

    const response = await apiPost<CreateDatasetResponse>(
        '/core/datasets/create',
        {
            name,
            language,
            region,
            default_reps: defaultReps,
            prompts_per_user: promptsPerUser,
            sequential_unique_prompts: sequentialUniquePrompts,
            collector_open_registration: collectorOpenRegistration,
            collectors_require_approval: collectorsRequireApproval,
            annotator_open_registration: annotatorOpenRegistration,
            annotators_require_approval: annotatorsRequireApproval,
        },
        cookieHeader
    );

    if (!response.ok) {
        return json(
            { error: response.error || 'Failed to create dataset' },
            { status: response.status || 500 }
        );
    }

    return json(response.data);
};
