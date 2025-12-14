import { apiGet } from '$lib/server/api';
import type { LayoutServerLoad } from './$types';

export interface UserInfo {
    id: string;
    email: string;
    name: string | null;
    validated: boolean;
    admin: boolean;
    unscoped_permissions: string[];
    visibility_permissions: string[];
}

/** The tabs that can appear in the navbar */
export type NavTab =
    | 'datasets'
    | 'collection'
    | 'processing'
    | 'annotation'
    | 'visualization'
    | 'users'
    | 'questions';

/**
 * Computes which navbar tabs a user should see based on their permissions.
 * Admins see all tabs.
 */
function computeVisibleTabs(user: UserInfo): NavTab[] {
    const tabs: NavTab[] = [];

    // Admins see everything
    if (user.admin) {
        return ['datasets', 'collection', 'processing', 'annotation', 'visualization', 'users', 'questions'];
    }

    const unscoped = new Set(user.unscoped_permissions);
    const scoped = new Set(user.visibility_permissions);

    // Datasets: RESEARCHER | DATASET_EDITOR
    if (unscoped.has('RESEARCHER') || unscoped.has('DATASET_EDITOR')) {
        tabs.push('datasets');
    }

    // Collection: RESEARCHER | DATASET_EDITOR
    if (unscoped.has('RESEARCHER') || unscoped.has('DATASET_EDITOR')) {
        tabs.push('collection');
    }

    // Processing: RESEARCHER
    if (unscoped.has('RESEARCHER')) {
        tabs.push('processing');
    }

    // Annotation: RESEARCHER | ANNOTATE (scoped)
    if (unscoped.has('RESEARCHER') || scoped.has('ANNOTATE')) {
        tabs.push('annotation');
    }

    // Visualization: RESEARCHER | VISUALIZE_DATA (scoped)
    if (unscoped.has('RESEARCHER') || scoped.has('VISUALIZE_DATA')) {
        tabs.push('visualization');
    }

    // Users: RESEARCHER
    if (unscoped.has('RESEARCHER')) {
        tabs.push('users');
    }

    // Questions: ASK_QUESTIONS | ANSWER_QUESTIONS (scoped)
    if (scoped.has('ASK_QUESTIONS') || scoped.has('ANSWER_QUESTIONS')) {
        tabs.push('questions');
    }

    return tabs;
}

export const load: LayoutServerLoad = async ({ cookies }) => {
    const cookieHeader = cookies.get('session_id')
        ? `session_id=${cookies.get('session_id')}`
        : undefined;

    if (!cookieHeader) {
        return { user: null, visibleTabs: [] as NavTab[] };
    }

    const response = await apiGet<UserInfo>('/core/users/me', cookieHeader);

    if (response.ok && response.data) {
        const user = response.data;
        const visibleTabs = computeVisibleTabs(user);
        return { user, visibleTabs };
    }

    return { user: null, visibleTabs: [] as NavTab[] };
};
