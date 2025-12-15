<script lang="ts">
    import SidebarView from '$lib/components/SidebarView.svelte';
    import type { SidebarItemData } from '$lib/components/types';
    import { titleSuffix } from '$lib';
    import * as translations from '$lib/paraglide/messages.js';
    import { invalidateAll } from '$app/navigation';
    import { format } from 'timeago.js';
    import type { DatasetDetails, DatasetContentsInfo } from './api/datasets/[id]/about/+server';

    let { data } = $props();

    // View state: 'none' | 'create' | dataset id
    let activeView = $state<string>('none');
    let isSubmitting = $state(false);
    let errorMessage = $state('');
    let successMessage = $state('');

    // Dataset details when viewing a specific dataset
    let datasetDetails = $state<DatasetDetails | null>(null);
    let isLoadingDataset = $state(false);
    let isRefreshingSummary = $state(false);

    // Form fields for creating a dataset
    let name = $state('');
    let language = $state('');
    let region = $state('');
    let defaultReps = $state<number | null>(null);
    let promptsPerUser = $state<number | null>(null);
    let sequentialUniquePrompts = $state(false);
    let collectorOpenRegistration = $state(false);
    let collectorsRequireApproval = $state(true);
    let annotatorOpenRegistration = $state(false);
    let annotatorsRequireApproval = $state(true);

    // Build sidebar items from datasets + create button
    const sidebarItems = $derived<SidebarItemData[]>([
        { id: 'create', label: translations.create_dataset(), active: activeView === 'create' },
        ...data.datasets.map((ds) => ({
            id: ds.id,
            label: ds.name,
            active: activeView === ds.id
        }))
    ]);

    async function handleItemClick(id: string) {
        activeView = id;
        errorMessage = '';
        successMessage = '';
        datasetDetails = null;

        // If clicking on a dataset (not 'create' or 'none'), fetch its details
        if (id !== 'create' && id !== 'none') {
            await fetchDatasetDetails(id);
        }
    }

    async function fetchDatasetDetails(id: string) {
        isLoadingDataset = true;
        try {
            const response = await fetch(`/api/datasets/${id}/about`);
            if (!response.ok) {
                const error = await response.json();
                errorMessage = error.error || 'Failed to load dataset';
                return;
            }
            datasetDetails = await response.json();

            // If summary is stale, refresh it in the background
            if (datasetDetails?.contents.stale) {
                refreshSummary(id);
            }
        } catch (err) {
            errorMessage = 'Failed to connect to the server';
        } finally {
            isLoadingDataset = false;
        }
    }

    async function refreshSummary(id: string) {
        isRefreshingSummary = true;
        try {
            const response = await fetch(`/api/datasets/${id}/summarize`);
            if (response.ok && datasetDetails) {
                const summaryData = await response.json();
                datasetDetails = {
                    ...datasetDetails,
                    contents: {
                        ...datasetDetails.contents,
                        summary: summaryData.summary,
                        summary_updated: summaryData.summary_updated,
                        stale: summaryData.stale
                    }
                };
            }
        } catch (err) {
            // Silently fail for background refresh
        } finally {
            isRefreshingSummary = false;
        }
    }

    function formatRelativeTime(timestamp: number | null): string {
        if (!timestamp) return 'Never';
        return format(timestamp);
    }

    function formatRegistrationCode(code: string): string {
        if (code.length !== 8) return code;
        return `${code[0]}-${code.slice(1, 7)}-${code[7]}`;
    }

    function resetForm() {
        name = '';
        language = '';
        region = '';
        defaultReps = null;
        promptsPerUser = null;
        sequentialUniquePrompts = false;
        collectorOpenRegistration = false;
        collectorsRequireApproval = true;
        annotatorOpenRegistration = false;
        annotatorsRequireApproval = true;
    }

    async function handleCreateDataset(event: SubmitEvent) {
        event.preventDefault();
        errorMessage = '';
        successMessage = '';
        isSubmitting = true;

        try {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('language', language);
            if (region) formData.append('region', region);
            if (defaultReps !== null) formData.append('default_reps', defaultReps.toString());
            if (promptsPerUser !== null) formData.append('prompts_per_user', promptsPerUser.toString());
            formData.append('sequential_unique_prompts', sequentialUniquePrompts.toString());
            formData.append('collector_open_registration', collectorOpenRegistration.toString());
            formData.append('collectors_require_approval', collectorsRequireApproval.toString());
            formData.append('annotator_open_registration', annotatorOpenRegistration.toString());
            formData.append('annotators_require_approval', annotatorsRequireApproval.toString());

            const response = await fetch('/api/datasets/create', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                errorMessage = result.error ?? 'Failed to create dataset';
                return;
            }

            successMessage = 'Dataset created successfully!';
            resetForm();
            await invalidateAll();

            // Switch to viewing the new dataset
            if (result.id) {
                await handleItemClick(result.id);
            }
        } catch (err) {
            errorMessage = 'Failed to connect to the server';
        } finally {
            isSubmitting = false;
        }
    }
</script>

<svelte:head>
    <title>{translations.datasets()} &mdash; {titleSuffix()}</title>
</svelte:head>

<SidebarView
    fullWidth={false}
    sidebarTitle={translations.datasets()}
    sidebarItems={sidebarItems}
    onItemClick={handleItemClick}
>
    {#snippet mainContent()}
        {#if activeView === 'none'}
            <div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                <p>Select a dataset or create a new one</p>
            </div>
        {:else if activeView === 'create'}
            <div class="p-6">
                <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Create New Dataset</h2>

                <form class="space-y-6 max-w-2xl" onsubmit={handleCreateDataset}>
                    {#if errorMessage}
                        <div class="alert-error">
                            <p>{errorMessage}</p>
                        </div>
                    {/if}

                    {#if successMessage}
                        <div class="alert-success">
                            <p>{successMessage}</p>
                        </div>
                    {/if}

                    <!-- Basic Info -->
                    <fieldset class="space-y-4">
                        <legend class="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</legend>

                        <div>
                            <label for="name" class="label">Dataset Name <span class="text-red-500">*</span></label>
                            <input
                                id="name"
                                type="text"
                                required
                                bind:value={name}
                                class="input"
                                placeholder="e.g., ASL Signs Collection"
                            />
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label for="language" class="label">Language <span class="text-red-500">*</span></label>
                                <input
                                    id="language"
                                    type="text"
                                    required
                                    bind:value={language}
                                    class="input"
                                    placeholder="e.g., ASL"
                                />
                            </div>

                            <div>
                                <label for="region" class="label">Region/Dialect</label>
                                <input
                                    id="region"
                                    type="text"
                                    bind:value={region}
                                    class="input"
                                    placeholder="e.g., East Coast"
                                />
                            </div>
                        </div>
                    </fieldset>

                    <!-- Collection Settings -->
                    <fieldset class="space-y-4">
                        <legend class="text-lg font-semibold text-gray-900 dark:text-white">Collection Settings</legend>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label for="defaultReps" class="label">Default Repetitions</label>
                                <input
                                    id="defaultReps"
                                    type="number"
                                    min="1"
                                    bind:value={defaultReps}
                                    class="input"
                                    placeholder="Uses system default"
                                />
                                <p class="helper-text">Number of times each prompt should be recorded</p>
                            </div>

                            <div>
                                <label for="promptsPerUser" class="label">Prompts Per User</label>
                                <input
                                    id="promptsPerUser"
                                    type="number"
                                    min="-1"
                                    bind:value={promptsPerUser}
                                    class="input"
                                    placeholder="-1 for all prompts"
                                />
                                <p class="helper-text">-1 or empty = all prompts</p>
                            </div>
                        </div>

                        <div class="flex items-center gap-2">
                            <input
                                id="sequentialUniquePrompts"
                                type="checkbox"
                                bind:checked={sequentialUniquePrompts}
                                class="rounded border-gray-300 dark:border-gray-600"
                            />
                            <label for="sequentialUniquePrompts" class="text-sm text-gray-700 dark:text-gray-300">
                                Assign prompts sequentially (unique per user)
                            </label>
                        </div>
                    </fieldset>

                    <!-- Collector Registration -->
                    <fieldset class="space-y-4">
                        <legend class="text-lg font-semibold text-gray-900 dark:text-white">Collector Registration</legend>

                        <div class="flex items-center gap-2">
                            <input
                                id="collectorOpenRegistration"
                                type="checkbox"
                                bind:checked={collectorOpenRegistration}
                                class="rounded border-gray-300 dark:border-gray-600"
                            />
                            <label for="collectorOpenRegistration" class="text-sm text-gray-700 dark:text-gray-300">
                                Allow open registration for data collectors
                            </label>
                        </div>

                        <div class="flex items-center gap-2">
                            <input
                                id="collectorsRequireApproval"
                                type="checkbox"
                                bind:checked={collectorsRequireApproval}
                                class="rounded border-gray-300 dark:border-gray-600"
                            />
                            <label for="collectorsRequireApproval" class="text-sm text-gray-700 dark:text-gray-300">
                                Require manual approval for collectors
                            </label>
                        </div>
                    </fieldset>

                    <!-- Annotator Registration -->
                    <fieldset class="space-y-4">
                        <legend class="text-lg font-semibold text-gray-900 dark:text-white">Annotator Registration</legend>

                        <div class="flex items-center gap-2">
                            <input
                                id="annotatorOpenRegistration"
                                type="checkbox"
                                bind:checked={annotatorOpenRegistration}
                                class="rounded border-gray-300 dark:border-gray-600"
                            />
                            <label for="annotatorOpenRegistration" class="text-sm text-gray-700 dark:text-gray-300">
                                Allow open registration for annotators
                            </label>
                        </div>

                        <div class="flex items-center gap-2">
                            <input
                                id="annotatorsRequireApproval"
                                type="checkbox"
                                bind:checked={annotatorsRequireApproval}
                                class="rounded border-gray-300 dark:border-gray-600"
                            />
                            <label for="annotatorsRequireApproval" class="text-sm text-gray-700 dark:text-gray-300">
                                Require manual approval for annotators
                            </label>
                        </div>
                    </fieldset>

                    <div class="pt-4">
                        <button type="submit" disabled={isSubmitting} class="btn-primary">
                            {#if isSubmitting}
                                Creating...
                            {:else}
                                Create Dataset
                            {/if}
                        </button>
                    </div>
                </form>
            </div>
        {:else}
            <!-- Dataset details view -->
            {#if isLoadingDataset}
                <div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                    <p>Loading dataset...</p>
                </div>
            {:else if errorMessage}
                <div class="p-6">
                    <div class="alert-error">
                        <p>{errorMessage}</p>
                    </div>
                </div>
            {:else if datasetDetails}
                <div class="p-6 space-y-8 overflow-auto">
                    <!-- Header -->
                    <div>
                        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{datasetDetails.name}</h2>
                        <p class="text-gray-600 dark:text-gray-400">
                            {datasetDetails.language}{datasetDetails.region ? ` (${datasetDetails.region})` : ''}
                        </p>
                        {#if datasetDetails.can_edit}
                            <span class="inline-block mt-2 text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                                Can edit
                            </span>
                        {/if}
                    </div>

                    <!-- Summary Section -->
                    <section class="bg-gray-50 dark:bg-slate-800 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Dataset Summary</h3>
                            <div class="flex items-center gap-3">
                                <span class="text-sm text-gray-500 dark:text-gray-400">
                                    Last refreshed: {formatRelativeTime(datasetDetails.contents.summary_updated)}
                                </span>
                                <button
                                    type="button"
                                    class="btn-secondary text-sm"
                                    disabled={isRefreshingSummary}
                                    onclick={() => refreshSummary(datasetDetails!.id)}
                                >
                                    {#if isRefreshingSummary}
                                        Refreshing...
                                    {:else}
                                        Refresh
                                    {/if}
                                </button>
                            </div>
                        </div>

                        {#if datasetDetails.contents.summary}
                            <dl class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {#each Object.entries(datasetDetails.contents.summary) as [key, value]}
                                    <div>
                                        <dt class="text-sm text-gray-500 dark:text-gray-400">{key.replace(/_/g, ' ')}</dt>
                                        <dd class="text-lg font-medium text-gray-900 dark:text-white">{value}</dd>
                                    </div>
                                {/each}
                            </dl>
                        {:else}
                            <p class="text-gray-500 dark:text-gray-400">No summary available yet.</p>
                        {/if}
                    </section>

                    <!-- Basic Information -->
                    <section>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h3>
                        <dl class="grid grid-cols-2 gap-4">
                            <div>
                                <dt class="label">Dataset Name</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.name}</dd>
                            </div>
                            <div>
                                <dt class="label">Language</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.language}</dd>
                            </div>
                            <div>
                                <dt class="label">Region/Dialect</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.region || '—'}</dd>
                            </div>
                            <div>
                                <dt class="label">Permission Scope</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.scope.name}</dd>
                            </div>
                        </dl>
                    </section>

                    <!-- Collection Settings -->
                    <section>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Collection Settings</h3>
                        <dl class="grid grid-cols-2 gap-4">
                            <div>
                                <dt class="label">Default Repetitions</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.default_repetitions}</dd>
                            </div>
                            <div>
                                <dt class="label">Prompts Per User</dt>
                                <dd class="text-gray-900 dark:text-white">
                                    {datasetDetails.prompts_assigned === -1 ? 'All prompts' : datasetDetails.prompts_assigned}
                                </dd>
                            </div>
                            <div>
                                <dt class="label">Sequential Unique Prompts</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.sequential_unique_prompts ? 'Yes' : 'No'}</dd>
                            </div>
                        </dl>
                    </section>

                    <!-- Collector Registration -->
                    <section>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Collector Registration</h3>
                        <dl class="grid grid-cols-2 gap-4">
                            <div>
                                <dt class="label">Open Registration</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.collector_reg_open ? 'Yes' : 'No'}</dd>
                            </div>
                            {#if datasetDetails.collector_reg_open && datasetDetails.collector_code}
                                <div>
                                    <dt class="label">Registration Code</dt>
                                    <dd class="text-gray-900 dark:text-white font-mono">{formatRegistrationCode(datasetDetails.collector_code)}</dd>
                                </div>
                            {/if}
                            <div>
                                <dt class="label">Require Approval</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.collector_req_approval ? 'Yes' : 'No'}</dd>
                            </div>
                        </dl>
                    </section>

                    <!-- Annotator Registration -->
                    <section>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Annotator Registration</h3>
                        <dl class="grid grid-cols-2 gap-4">
                            <div>
                                <dt class="label">Open Registration</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.annotator_reg_open ? 'Yes' : 'No'}</dd>
                            </div>
                            {#if datasetDetails.annotator_reg_open && datasetDetails.annotator_code}
                                <div>
                                    <dt class="label">Registration Code</dt>
                                    <dd class="text-gray-900 dark:text-white font-mono">{formatRegistrationCode(datasetDetails.annotator_code)}</dd>
                                </div>
                            {/if}
                            <div>
                                <dt class="label">Require Approval</dt>
                                <dd class="text-gray-900 dark:text-white">{datasetDetails.annotator_req_approval ? 'Yes' : 'No'}</dd>
                            </div>
                        </dl>
                    </section>

                    <!-- Prompts -->
                    {#if datasetDetails.prompt_data.length > 0}
                        <section>
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                                Prompts ({datasetDetails.prompt_data.length})
                            </h3>
                            <div class="overflow-x-auto">
                                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                    <thead>
                                        <tr>
                                            <th class="px-4 py-2 text-left text-sm font-medium text-gray-500 dark:text-gray-400">Internal Name</th>
                                            <th class="px-4 py-2 text-left text-sm font-medium text-gray-500 dark:text-gray-400">Display Text</th>
                                            <th class="px-4 py-2 text-left text-sm font-medium text-gray-500 dark:text-gray-400">Reference Type</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                                        {#each datasetDetails.prompt_data as prompt}
                                            <tr>
                                                <td class="px-4 py-2 text-sm text-gray-900 dark:text-white font-mono">{prompt.internal_name}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">{prompt.display_text}</td>
                                                <td class="px-4 py-2 text-sm text-gray-900 dark:text-white">{prompt.reference_type}</td>
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    {/if}

                    <!-- Review Classifications -->
                    {#if datasetDetails.review_classifications.length > 0}
                        <section>
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Review Classifications</h3>
                            <div class="flex flex-wrap gap-2">
                                {#each datasetDetails.review_classifications as classification}
                                    <span class="px-2 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded">
                                        {classification}
                                    </span>
                                {/each}
                            </div>
                        </section>
                    {/if}

                    <!-- Device Bans -->
                    {#if datasetDetails.device_bans.length > 0}
                        <section>
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Banned Devices</h3>
                            <div class="flex flex-wrap gap-2">
                                {#each datasetDetails.device_bans as device}
                                    <span class="px-2 py-1 text-sm bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded font-mono">
                                        {device}
                                    </span>
                                {/each}
                            </div>
                        </section>
                    {/if}
                </div>
            {/if}
        {/if}
    {/snippet}
</SidebarView>
