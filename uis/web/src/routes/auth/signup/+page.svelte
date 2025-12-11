<script lang="ts">
	import { goto } from '$app/navigation';

	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let registrationCode = $state('');

	let isSubmitting = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	// Client-side validation
	let passwordMismatch = $derived(confirmPassword !== '' && password !== confirmPassword);
	let passwordTooShort = $derived(password !== '' && password.length < 12);

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = '';
		successMessage = '';

		// Client-side checks
		if (passwordMismatch) {
			errorMessage = 'Passwords do not match';
			return;
		}

		if (passwordTooShort) {
			errorMessage = 'Password must be at least 12 characters';
			return;
		}

		isSubmitting = true;

		try {
			const formData = new FormData();
			formData.append('email', email);
			formData.append('password', password);
			if (registrationCode) {
				formData.append('registration_code', registrationCode);
			}

			const response = await fetch('/api/auth/signup', {
				method: 'POST',
				body: formData
			});

			const result = await response.json();

			if (!response.ok) {
				errorMessage = result.error ?? 'An error occurred during signup';
				return;
			}

			successMessage = 'Account created! Please check your email to confirm your account.';

			// Redirect to login after a brief delay
			setTimeout(() => {
				goto('/auth/login');
			}, 2000);
		} catch (err) {
			errorMessage = 'Failed to connect to the server';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<svelte:head>
	<title>Sign Up | Signosure</title>
</svelte:head>

<div class="flex min-h-full items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
	<div class="w-full max-w-md space-y-8">
		<div>
			<h2 class="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
				Create your account
			</h2>
		</div>

		<form class="mt-8 space-y-6" onsubmit={handleSubmit}>
			{#if errorMessage}
				<div class="rounded-md bg-red-50 dark:bg-red-900/50 p-4">
					<p class="text-sm text-red-700 dark:text-red-200">{errorMessage}</p>
				</div>
			{/if}

			{#if successMessage}
				<div class="rounded-md bg-green-50 dark:bg-green-900/50 p-4">
					<p class="text-sm text-green-700 dark:text-green-200">{successMessage}</p>
				</div>
			{/if}

			<div class="space-y-4">
				<div>
					<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
						Email address
					</label>
					<input
						id="email"
						name="email"
						type="email"
						autocomplete="email"
						required
						bind:value={email}
						class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2
						       text-gray-900 placeholder-gray-400
						       focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
						       dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
						placeholder="you@example.com"
					/>
				</div>

				<div>
					<label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
						Password
					</label>
					<input
						id="password"
						name="password"
						type="password"
						autocomplete="new-password"
						required
						bind:value={password}
						class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2
						       text-gray-900 placeholder-gray-400
						       focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
						       dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
						class:border-yellow-500={passwordTooShort}
						class:dark:border-yellow-500={passwordTooShort}
						placeholder="Minimum 12 characters"
					/>
					{#if passwordTooShort}
						<p class="mt-1 text-sm text-yellow-600 dark:text-yellow-400">
							Password must be at least 12 characters
						</p>
					{/if}
				</div>

				<div>
					<label
						for="confirm-password"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						Confirm password
					</label>
					<input
						id="confirm-password"
						name="confirm-password"
						type="password"
						autocomplete="new-password"
						required
						bind:value={confirmPassword}
						class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2
						       text-gray-900 placeholder-gray-400
						       focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
						       dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
						class:border-red-500={passwordMismatch}
						class:dark:border-red-500={passwordMismatch}
					/>
					{#if passwordMismatch}
						<p class="mt-1 text-sm text-red-600 dark:text-red-400">Passwords do not match</p>
					{/if}
				</div>

				<div>
					<label
						for="registration-code"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						Registration code
						<span class="text-gray-400 dark:text-gray-500">(optional)</span>
					</label>
					<input
						id="registration-code"
						name="registration_code"
						type="text"
						bind:value={registrationCode}
						class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2
						       text-gray-900 placeholder-gray-400 uppercase
						       focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
						       dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
						placeholder="ABC-1234"
					/>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						If you were given a code to join a dataset, enter it here
					</p>
				</div>
			</div>

			<div>
				<button
					type="submit"
					disabled={isSubmitting || passwordMismatch || passwordTooShort}
					class="group relative flex w-full justify-center rounded-md bg-blue-600 px-3 py-2
					       text-sm font-semibold text-white
					       hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
					       disabled:cursor-not-allowed disabled:opacity-50
					       dark:focus:ring-offset-gray-900"
				>
					{#if isSubmitting}
						Creating account...
					{:else}
						Sign up
					{/if}
				</button>
			</div>

			<p class="text-center text-sm text-gray-600 dark:text-gray-400">
				Already have an account?
				<a href="/auth/login" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
					Sign in
				</a>
			</p>
		</form>
	</div>
</div>
