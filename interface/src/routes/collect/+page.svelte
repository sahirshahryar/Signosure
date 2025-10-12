<script>
  import SidebarView from '$lib/components/SidebarView.svelte';
  import { titleSuffix } from '$lib';
  import * as translations from '$lib/paraglide/messages.js'
</script>
<svelte:head>
    <title>{translations.datasets()} &mdash; {titleSuffix()}</title>
</svelte:head>
<SidebarView fullWidth={false} sidebarTitle={translations.datasets()}
    sidebarContents={
    [
      translations.create_dataset()
    ]
    }
    >
    {#snippet mainContent()}
        <span></span>
    {/snippet}
</SidebarView>
