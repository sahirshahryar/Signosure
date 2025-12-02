<script>
	import Sidebar from "$lib/components/Sidebar.svelte";

    let { fullWidth = $bindable(false), sidebarTitle, sidebarContents, mainContent } = $props();
</script>

<div class="flex h-full m-auto {fullWidth ? "px-4" : "max-w-7xl sm:px-6 lg:px-8"} transition-all">
    <Sidebar title={sidebarTitle} contents={sidebarContents} />
    <div class="main bg-slate-50 dark:bg-slate-950 h-full flex-1 ml-4 rounded-lg border-2 border-slate-200 dark:border-slate-800 shadow-lg overflow-auto">
        {@render mainContent?.()}
    </div>
</div>
