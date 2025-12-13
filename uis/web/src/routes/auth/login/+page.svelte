<script lang="ts">
    import { goto, invalidateAll } from '$app/navigation';

    let email = $state('');
    let password = $state('');

    let isSubmitting = $state(false);
    let errorMessage = $state('');

    async function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        errorMessage = '';
        isSubmitting = true;

        try {
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                // Map error codes to user-friendly messages
                if (result.error === 'users.login.invalid') {
                    errorMessage = 'Invalid email or password';
                } else if (result.error === 'users.login.disabled') {
                    errorMessage = 'Your account has been disabled';
                } else {
                    errorMessage = result.error ?? 'An error occurred during login';
                }
                return;
            }

            // Invalidate all data to refresh the layout (user info in navbar)
            await invalidateAll();

            // Check if email is validated
            if (!result.validated) {
                // Redirect to a page asking them to verify their email
                goto('/auth/verify-email');
                return;
            }

            // Successful login - redirect to dashboard or home
            goto('/');
        } catch (err) {
            errorMessage = 'Failed to connect to the server';
        } finally {
            isSubmitting = false;
        }
    }
</script>

<svelte:head>
    <title>Sign In | Signosure</title>
</svelte:head>

<div class="flex min-h-full items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
    <div class="w-full max-w-md space-y-8">
        <div>
            <h2 class="mt-6 page-heading">Sign in to your account</h2>
        </div>

        <form class="mt-8 space-y-6" onsubmit={handleSubmit}>
            {#if errorMessage}
                <div class="alert-error">
                    <p>{errorMessage}</p>
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
                        autocomplete="current-password"
                        required
                        bind:value={password}
                        class="input"
                    />
                </div>
            </div>

            <div class="flex items-center justify-between">
                <div class="text-sm">
                    <a href="/auth/forgot-password" class="link">Forgot your password?</a>
                </div>
            </div>

            <div>
                <button type="submit" disabled={isSubmitting} class="btn-primary btn-full">
                    {#if isSubmitting}
                        Signing in...
                    {:else}
                        Sign in
                    {/if}
                </button>
            </div>

            <p class="text-center text-sm text-gray-600 dark:text-gray-400">
                Don't have an account?
                <a href="/auth/signup" class="link">Sign up</a>
            </p>
        </form>
    </div>
</div>
