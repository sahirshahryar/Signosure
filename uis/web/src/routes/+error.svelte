<script lang="ts">
    import { page } from '$app/stores';
</script>

<svelte:head>
    <title>Page Not Found | Signosure</title>
</svelte:head>

<div class="flex min-h-full items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
    <div class="w-full max-w-md space-y-8 text-center">
        <div>
            <h1 class="text-6xl font-bold text-gray-900 dark:text-white">{$page.status}</h1>
            <h2 class="mt-4 page-heading">
                {#if $page.status === 404}
                    Page not found
                {:else}
                    Something went wrong
                {/if}
            </h2>
            <p class="mt-4 text-gray-600 dark:text-gray-400">
                {#if $page.status === 404}
                    The page you're looking for doesn't exist or has been moved.
                {:else}
                    {$page.error?.message ?? 'An unexpected error occurred.'}
                {/if}
            </p>
        </div>

        <div>
            <a href="/" class="btn-primary btn-full inline-flex justify-center">
                Return home
            </a>
        </div>
    </div>
</div>
