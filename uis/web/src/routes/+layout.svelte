<script lang="ts">
    import Navbar from "$lib/components/Navbar.svelte";
	import { i18n } from "$lib/i18n";
	import { ParaglideJS } from "@inlang/paraglide-sveltekit";
	import * as translations from "$lib/paraglide/messages";
	import '../app.css';

	let { children, data } = $props();
</script>

<style lang="postcss">
    :global(body) {
        @apply bg-gray-100 dark:bg-gray-900;
    }
</style>

<ParaglideJS {i18n}>
    <div class="flex flex-col items-stretch h-screen w-screen ">
        <Navbar user={data.user} visibleTabs={data.visibleTabs} />
        <div class="flex-1 my-4" id="ui-container">
          {@render children()}
        </div>
    </div>
</ParaglideJS>
