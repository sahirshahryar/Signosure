<script lang="ts">
    import SidebarItem from "$lib/components/SidebarItem.svelte";
    import type { SidebarItemData } from "./types";

    let {
        title,
        items = [],
        onItemClick
    }: {
        title: string;
        items: SidebarItemData[];
        onItemClick?: (id: string) => void;
    } = $props();
</script>

<div class="sidebar bg-slate-200 dark:bg-slate-800 dark:text-white rounded-lg min-w-52 w-1/5 max-w-80 h-full shadow-2xl overflow-auto">
    <div class="pt-4 pb-6 px-5 text-3xl font-bold">{title}</div>
    {#each items as item}
        <SidebarItem {item} onclick={onItemClick} />
    {/each}
</div>
