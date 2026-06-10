<script>
  export let navigate;

  let email = '';
  let password = '';
  let loading = false;
  let error = '';

  async function handleLogin(e) {
    e.preventDefault();
    loading = true;
    error = '';

    try {
      // Aici poți integra apelul tău către API-ul FastAPI (ex: /token sau /login)
      // Pentru moment, simulăm o autentificare reușită:
      if (email && password) {
        navigate('dashboard');
      } else {
        throw new Error('Te rugăm să completezi toate câmpurile.');
      }
    } catch (err) {
      error = err.message || 'A apărut o eroare la autentificare.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-background">
  <div class="w-full max-w-md space-y-8 bg-card text-card-foreground border border-border p-8 rounded-xl shadow-sm">
    <div class="text-center">
      <h2 class="text-3xl font-extrabold tracking-tight text-foreground">
        Conectează-te
      </h2>
      <p class="mt-2 text-sm text-muted-foreground">
        Sau
        <button on:click={() => navigate('register')} class="font-medium text-primary hover:underline">
          creează un cont nou
        </button>
      </p>
    </div>

    {#if error}
      <div class="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
        {error}
      </div>
    {/if}

    <form class="mt-8 space-y-6" on:submit={handleLogin}>
      <div class="space-y-4 rounded-md shadow-sm">
        <div>
          <label for="email-address" class="block text-sm font-medium text-foreground mb-1">Email</label>
          <input
            id="email-address"
            name="email"
            type="email"
            required
            bind:value={email}
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            placeholder="nume@exemplu.com"
          />
        </div>
        <div>
          <label for="password" class="block text-sm font-medium text-foreground mb-1">Parolă</label>
          <input
            id="password"
            name="password"
            type="password"
            required
            bind:value={password}
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            placeholder="••••••••"
          />
        </div>
      </div>

      <div>
        <button
          type="submit"
          disabled={loading}
          class="relative flex w-full justify-center rounded-md bg-primary py-2 px-4 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 transition-colors"
        >
          {loading ? 'Se încarcă...' : 'Intră în cont'}
        </button>
      </div>
    </form>
  </div>
</div>