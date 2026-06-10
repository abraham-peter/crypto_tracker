<script>
  export let navigate;

  let name = '';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let loading = false;
  let error = '';

  async function handleRegister(e) {
    e.preventDefault();
    loading = true;
    error = '';

    if (password !== confirmPassword) {
      error = 'Parolele nu se potrivesc.';
      loading = false;
      return;
    }

    try {
      // Simulare apel API de înregistrare
      if (email && password) {
        navigate('login');
      } else {
        throw new Error('Toate câmpurile sunt obligatorii.');
      }
    } catch (err) {
      error = err.message || 'Înregistrarea a eșuat.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-background">
  <div class="w-full max-w-md space-y-8 bg-card text-card-foreground border border-border p-8 rounded-xl shadow-sm">
    <div class="text-center">
      <h2 class="text-3xl font-extrabold tracking-tight text-foreground">
        Creează un cont
      </h2>
      <p class="mt-2 text-sm text-muted-foreground">
        Ai deja cont?
        <button on:click={() => navigate('login')} class="font-medium text-primary hover:underline">
          Autentifică-te
        </button>
      </p>
    </div>

    {#if error}
      <div class="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
        {error}
      </div>
    {/if}

    <form class="mt-8 space-y-4" on:submit={handleRegister}>
      <div>
        <label for="name" class="block text-sm font-medium text-foreground mb-1">Nume complet</label>
        <input
          id="name"
          type="text"
          required
          bind:value={name}
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="Ion Popescu"
        />
      </div>

      <div>
        <label for="email" class="block text-sm font-medium text-foreground mb-1">Email</label>
        <input
          id="email"
          type="email"
          required
          bind:value={email}
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="nume@exemplu.com"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-medium text-foreground mb-1">Parolă</label>
        <input
          id="password"
          type="password"
          required
          bind:value={password}
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="••••••••"
        />
      </div>

      <div>
        <label for="confirm-password" class="block text-sm font-medium text-foreground mb-1">Confirmă parola</label>
        <input
          id="confirm-password"
          type="password"
          required
          bind:value={confirmPassword}
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="••••••••"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        class="w-full justify-center rounded-md bg-primary py-2 px-4 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 transition-colors"
      >
        {loading ? 'Se înregistrează...' : 'Înregistrează-te'}
      </button>
    </form>
  </div>
</div>