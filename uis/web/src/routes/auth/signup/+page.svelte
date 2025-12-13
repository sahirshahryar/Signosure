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

		console.log("Password seems valid.");

		isSubmitting = true;

		try {
		    console.log("Trying to submit form.")
			const formData = new FormData();
			formData.append('email', email);
			formData.append('password', password);
			if (registrationCode) {
				formData.append('registration_code', registrationCode);
			}

			console.log("About to submit")

			const response = await fetch('/api/auth/signup', {
				method: 'POST',
				body: formData
			});

			console.log("await fetch complete")

			const result = await response.json();

			console.log("Received response")

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
			<h2 class="mt-6 page-heading">Create your account</h2>
		</div>

		<form class="mt-8 space-y-6" onsubmit={handleSubmit}>
			{#if errorMessage}
				<div class="alert-error">
					<p>{errorMessage}</p>
				</div>
			{/if}

			{#if successMessage}
				<div class="alert-success">
					<p>{successMessage}</p>
				</div>
			{/if}

			<div class="space-y-4">
				<div>
					<label for="email" class="label">Email address</label>
					<input
						id="email"
						name="email"
						type="email"
						autocomplete="email"
						required
						bind:value={email}
						class="input"
						placeholder="you@example.com"
					/>
				</div>

				<div>
					<label for="password" class="label">Password</label>
					<input
						id="password"
						name="password"
						type="password"
						autocomplete="new-password"
						required
						bind:value={password}
						class="input"
						class:input-warning={passwordTooShort}
						placeholder="Minimum 12 characters"
					/>
					{#if passwordTooShort}
						<p class="validation-warning">Password must be at least 12 characters</p>
					{/if}
				</div>

				<div>
					<label for="confirm-password" class="label">Confirm password</label>
					<input
						id="confirm-password"
						name="confirm-password"
						type="password"
						autocomplete="new-password"
						required
						bind:value={confirmPassword}
						class="input"
						class:input-error={passwordMismatch}
					/>
					{#if passwordMismatch}
						<p class="validation-error">Passwords do not match</p>
					{/if}
				</div>

				<div>
					<label for="registration-code" class="label">
						Registration code
						<span class="text-gray-400 dark:text-gray-500">(optional)</span>
					</label>
					<input
						id="registration-code"
						name="registration_code"
						type="text"
						bind:value={registrationCode}
						class="input uppercase"
						placeholder="ABC-1234"
					/>
					<p class="helper-text">If you were given a code to join a dataset, enter it here</p>
				</div>
			</div>

			<div>
				<button
					type="submit"
					disabled={isSubmitting || passwordMismatch || passwordTooShort}
					class="btn-primary btn-full"
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
				<a href="/auth/login" class="link">Sign in</a>
			</p>
		</form>
	</div>
</div>
