<script lang="ts">
    import type { SidebarItemData } from "./types";

    let { item, onclick }: { item: SidebarItemData; onclick?: (id: string) => void } = $props();
</script>

<button
    type="button"
    class="w-full text-left px-5 py-2 text-sm transition-colors duration-150
           {item.active
               ? 'bg-slate-300 dark:bg-slate-700 font-medium'
               : 'hover:bg-slate-300/50 dark:hover:bg-slate-700/50'}"
    onclick={() => onclick?.(item.id)}
>
    {item.label}
</button>
