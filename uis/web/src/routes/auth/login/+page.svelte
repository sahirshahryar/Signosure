<script lang="ts">
    import { goto } from '$app/navigation';

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
            <h2 class="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
                Sign in to your account
            </h2>
        </div>

        <form class="mt-8 space-y-6" onsubmit={handleSubmit}>
            {#if errorMessage}
                <div class="rounded-md bg-red-50 dark:bg-red-900/50 p-4">
                    <p class="text-sm text-red-700 dark:text-red-200">{errorMessage}</p>
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
                        autocomplete="current-password"
                        required
                        bind:value={password}
                        class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2
                               text-gray-900 placeholder-gray-400
                               focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500
                               dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
                    />
                </div>
            </div>

            <div class="flex items-center justify-between">
                <div class="text-sm">
                    <a
                        href="/auth/forgot-password"
                        class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
                    >
                        Forgot your password?
                    </a>
                </div>
            </div>

            <div>
                <button
                    type="submit"
                    disabled={isSubmitting}
                    class="group relative flex w-full justify-center rounded-md bg-blue-600 px-3 py-2
                           text-sm font-semibold text-white
                           hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                           disabled:cursor-not-allowed disabled:opacity-50
                           dark:focus:ring-offset-gray-900"
                >
                    {#if isSubmitting}
                        Signing in...
                    {:else}
                        Sign in
                    {/if}
                </button>
            </div>

            <p class="text-center text-sm text-gray-600 dark:text-gray-400">
                Don't have an account?
                <a
                    href="/auth/signup"
                    class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
                >
                    Sign up
                </a>
            </p>
        </form>
    </div>
</div>
