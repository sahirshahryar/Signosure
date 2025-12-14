<script lang="ts">
    import Sidebar, { type SidebarItemData } from "$lib/components/Sidebar.svelte";

    let {
        fullWidth = false,
        sidebarTitle,
        sidebarItems,
        onItemClick,
        mainContent
    }: {
        fullWidth?: boolean;
        sidebarTitle: string;
        sidebarItems: SidebarItemData[];
        onItemClick?: (id: string) => void;
        mainContent?: () => any;
    } = $props();
</script>

<div class="flex h-full m-auto {fullWidth ? 'px-4' : 'max-w-7xl sm:px-6 lg:px-8'} transition-all">
    <Sidebar title={sidebarTitle} items={sidebarItems} {onItemClick} />
    <div class="main bg-slate-50 dark:bg-slate-950 h-full flex-1 ml-4 rounded-lg border-2 border-slate-200 dark:border-slate-800 shadow-lg overflow-auto">
        {@render mainContent?.()}
    </div>
</div>
