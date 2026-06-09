<script>
  import { onMount } from 'svelte';
  import Login from './components/Login.svelte';
  import Register from './components/Register.svelte';
  import Dashboard from './components/Dashboard.svelte';

  let currentRoute = 'login';

  // Funcție de navigare reactivă
  function navigate(route) {
    window.location.hash = `/${route}`;
  }

  function handleHashChange() {
    const hash = window.location.hash;
    if (hash === '#/register') {
      currentRoute = 'register';
    } else if (hash === '#/dashboard') {
      currentRoute = 'dashboard';
    } else {
      currentRoute = 'login';
    }
  }

  onMount(() => {
    window.addEventListener('hashchange', handleHashChange);
    handleHashChange(); // Verificare inițială la încărcarea paginii

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  });
</script>

<main class="min-h-screen bg-background text-foreground font-sans antialiased selection:bg-primary/20">
  {#if currentRoute === 'login'}
    <Login {navigate} />
  {:else if currentRoute === 'register'}
    <Register {navigate} />
  {:else if currentRoute === 'dashboard'}
    <Dashboard {navigate} />
  {/if}
</main>