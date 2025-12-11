<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let status = $state<'logging-out' | 'done' | 'error'>('logging-out');

	onMount(async () => {
		try {
			const response = await fetch('/api/auth/logout', {
				method: 'POST'
			});

			if (response.ok) {
				status = 'done';
				// Redirect to login after a brief moment
				setTimeout(() => goto('/auth/login'), 1000);
			} else {
				status = 'error';
			}
		} catch {
			status = 'error';
		}
	});
</script>

<svelte:head>
	<title>Logging out... | Signosure</title>
</svelte:head>

<div class="flex min-h-full items-center justify-center px-4 py-12">
	<div class="text-center">
		{#if status === 'logging-out'}
			<p class="text-lg text-gray-600 dark:text-gray-400">Logging out...</p>
		{:else if status === 'done'}
			<p class="text-lg text-green-600 dark:text-green-400">You have been logged out.</p>
			<p class="mt-2 text-sm text-gray-500 dark:text-gray-500">Redirecting to login...</p>
		{:else}
			<p class="text-lg text-red-600 dark:text-red-400">Something went wrong.</p>
			<a
				href="/auth/login"
				class="mt-4 inline-block text-blue-600 hover:text-blue-500 dark:text-blue-400"
			>
				Go to login
			</a>
		{/if}
	</div>
</div>
