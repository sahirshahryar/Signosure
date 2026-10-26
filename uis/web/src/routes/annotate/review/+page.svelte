<script lang="ts">
    import SidebarView from '$lib/components/SidebarView.svelte';
    import type { SidebarItemData } from '$lib/components/types';
    import { titleSuffix } from '$lib';

    let { data } = $props();

    // View state
    let activeView = $state<string>('none');

    // TODO: populate sidebar items
    const sidebarItems = $derived<SidebarItemData[]>([]);

    function handleItemClick(id: string) {
        activeView = id;
    }
</script>

<svelte:head>
    <title>Review &mdash; {titleSuffix()}</title>
</svelte:head>

<SidebarView
    fullWidth={false}
    sidebarTitle="Review"
    sidebarItems={sidebarItems}
    onItemClick={handleItemClick}
>
    {#snippet mainContent()}
        {#if activeView === 'none'}
            <div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                <p>Select an item</p>
            </div>
        {:else}
            <div class="p-6">
                <!-- TODO: review content -->
            </div>
        {/if}
    {/snippet}
</SidebarView>
