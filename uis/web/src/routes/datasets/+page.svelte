<script lang="ts">
    import SidebarView from '$lib/components/SidebarView.svelte';
    import type { SidebarItemData } from '$lib/components/types';
    import { titleSuffix } from '$lib';
    import * as translations from '$lib/paraglide/messages.js';
    import { invalidateAll } from '$app/navigation';

    let { data } = $props();

    // View state: 'none' | 'create' | dataset id
    let activeView = $state<string>('none');
    let isSubmitting = $state(false);
    let errorMessage = $state('');
    let successMessage = $state('');

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

    function handleItemClick(id: string) {
        activeView = id;
        errorMessage = '';
        successMessage = '';
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

            console.log(`Form data: ${name}, ${language}, ${region},`);

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
                activeView = result.id;
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
            <!-- Dataset view - placeholder for now -->
            {@const dataset = data.datasets.find(ds => ds.id === activeView)}
            {#if dataset}
                <div class="p-6">
                    <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">{dataset.name}</h2>
                    <p class="text-gray-600 dark:text-gray-400">
                        {dataset.language}{dataset.region ? ` (${dataset.region})` : ''}
                    </p>
                    <p class="mt-4 text-gray-500 dark:text-gray-500">
                        Dataset editing coming soon...
                    </p>
                </div>
            {/if}
        {/if}
    {/snippet}
</SidebarView>
