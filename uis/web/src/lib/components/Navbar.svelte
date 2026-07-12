<script lang="ts">
  import { VERSION, CLIENT, CLIENT_SHORT } from "$lib";
  import * as translations from "$lib/paraglide/messages";
  import { goto, invalidateAll } from "$app/navigation";
  import { page } from "$app/stores";

  type NavTab =
    | 'datasets'
    | 'glossary'
    | 'collection'
    | 'processing'
    | 'annotation'
    | 'visualization'
    | 'users'
    | 'questions';

  interface UserInfo {
    id: string;
    email: string;
    name: string | null;
    validated: boolean;
    admin: boolean;
  }

  let { user, visibleTabs = [] }: { user: UserInfo | null; visibleTabs: NavTab[] } = $props();

  // Tab configuration: maps tab ID to its route and translation function
  const tabConfig: Record<NavTab, { href: string; label: () => string }> = {
    datasets: { href: '/datasets', label: translations.datasets },
    glossary: { href: '/glossary', label: translations.glossary },
    collection: { href: '/collection', label: translations.collection },
    processing: { href: '/processing', label: translations.processing },
    annotation: { href: '/annotation', label: translations.annotation },
    visualization: { href: '/visualization', label: translations.visualization },
    users: { href: '/users', label: translations.users },
    questions: { href: '/questions', label: translations.questions },
  };

  // Check if a tab is currently active based on the current path
  function isActiveTab(href: string): boolean {
    const currentPath = $page.url.pathname;
    return currentPath === href || currentPath.startsWith(href + '/');
  }

  // Display name: use name if set, otherwise extract from email
  const displayName = $derived(
    user?.name ?? user?.email?.split('@')[0] ?? null
  );

  let dropdownOpen = $state(false);
  let dropdownRef: HTMLDivElement | undefined = $state();
  let closeTimeout: ReturnType<typeof setTimeout> | null = null;

  function openDropdown() {
    if (closeTimeout) {
      clearTimeout(closeTimeout);
      closeTimeout = null;
    }
    dropdownOpen = true;
  }

  function scheduleClose() {
    closeTimeout = setTimeout(() => {
      dropdownOpen = false;
    }, 150);
  }

  function toggleDropdown() {
    dropdownOpen = !dropdownOpen;
  }

  function closeDropdown(event: MouseEvent) {
    if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
      dropdownOpen = false;
    }
  }

  async function handleSignOut() {
    dropdownOpen = false;
    await fetch('/api/auth/logout', { method: 'POST' });
    await invalidateAll();
    goto('/auth/login');
  }

  $effect(() => {
    if (dropdownOpen) {
      document.addEventListener('click', closeDropdown);
      return () => document.removeEventListener('click', closeDropdown);
    }
  });
</script>

<div class="inline">
    <nav class="relative bg-gray-800 after:pointer-events-none after:absolute after:inset-x-0 after:bottom-0 after:h-px after:bg-white/10">
      <div class="mx-auto max-w-7xl px-2 sm:px-6 lg:px-8">
        <div class="relative flex h-16 items-center justify-between">
          <div class="flex flex-1 items-center justify-center sm:items-stretch sm:justify-start">
            <!-- TODO: Replace with custom logo  -->
            <div class="flex shrink-0 items-center">
              <img src="https://tailwindcss.com/plus-assets/img/logos/mark.svg?color=indigo&shade=500" alt="Your Company" class="h-8 w-auto" />
            </div>
            <div class="hidden sm:ml-6 sm:block">
              <div class="flex space-x-4">
                {#each visibleTabs as tab}
                  {@const config = tabConfig[tab]}
                  {@const active = isActiveTab(config.href)}
                  <a
                    href={config.href}
                    class={active ? 'nav-link-active' : 'nav-link'}
                    aria-current={active ? 'page' : undefined}
                  >
                    {config.label()}
                  </a>
                {/each}
              </div>
            </div>
          </div>
          <!-- User controls with dropdown -->
          <div
            id="user-controls"
            class="relative flex items-center pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0"
            role="navigation"
            aria-label="User menu"
            bind:this={dropdownRef}
            onmouseenter={openDropdown}
            onmouseleave={scheduleClose}
          >
            <button
              type="button"
              id="navbar-elements"
              class="rounded-md px-3 py-2 text-sm font-medium text-gray-300 cursor-pointer transition-colors duration-150 ease-in-out {dropdownOpen ? 'bg-white/5 text-white' : 'hover:bg-white/5 hover:text-white'}"
              onclick={toggleDropdown}
              aria-expanded={dropdownOpen}
              aria-haspopup="true"
            >
              {#if displayName}
                <div id="user-name" class="text-gray-100 text-right">{displayName}</div>
              {/if}
              <div id="client-name" class="text-gray-400 text-right"><span class="max-lg:hidden">{CLIENT}</span><span class="hidden max-lg:inline">{CLIENT_SHORT}</span></div>
            </button>

            <!-- Dropdown menu -->
            <div
              class="absolute text-right right-0 top-full z-10 mt-1 w-48 origin-top-right rounded-md bg-gray-800 py-1 shadow-lg ring-1 ring-white/10 focus:outline-none transition-all duration-150 ease-in-out"
              class:opacity-100={dropdownOpen}
              class:scale-100={dropdownOpen}
              class:opacity-0={!dropdownOpen}
              class:scale-95={!dropdownOpen}
              class:pointer-events-none={!dropdownOpen}
              role="menu"
              aria-orientation="vertical"
              aria-labelledby="navbar-elements"
            >
                {#if user}
                  <div class="px-4 pt-2 pb-3 text-xs text-gray-400 border-b border-white/10">
                    {user.email}
                  </div>
                  <a href="/settings" class="dropdown-item" role="menuitem">Account settings</a>
                  <button
                    onclick={handleSignOut}
                    class="dropdown-item w-full text-right"
                    role="menuitem"
                  >
                    Sign out
                  </button>
                {:else}
                  <a href="/auth/login" class="dropdown-item" role="menuitem">Sign in</a>
                  <a href="/auth/signup" class="dropdown-item" role="menuitem">Sign up</a>
                {/if}
              <div class="px-4 pt-3 pb-2 text-xs text-gray-500 border-t border-white/10">
                Signosure {VERSION}
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
</div>
