<script>
	import SidebarItem from "$lib/components/SidebarItem.svelte";

    let { title, contents = $bindable([]) } = $props();
</script>

<div class="sidebar bg-slate-200 dark:bg-slate-800 dark:text-white rounded-lg min-w-52 w-1/5 max-w-80 h-full shadow-2xl overflow-auto">
    <div class="pt-4 pb-6 px-5 text-3xl font-bold">{title}</div>
    {#each contents as content}
        <SidebarItem content={content}/>
    {/each}
</div>
