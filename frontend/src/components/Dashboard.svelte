<script>
  import { onMount } from 'svelte';

  export let navigate;

  let accounts = [];
  let selectedAccount = null;
  let transactions = [];
  let loading = true;
  let isConnecting = false;
  let loadingTransactions = false;
  let error = null;
  let statusMessage = "";

  const BACKEND_URL = "http://127.0.0.1:8000";

  // 1. Fetch connected accounts
  async function loadAccounts() {
    loading = true;
    error = null;
    try {
      const res = await fetch(`${BACKEND_URL}/accounts`);
      if (!res.ok) throw new Error("Could not load accounts.");
      const data = await res.json();
      accounts = data.accounts || [];

      if (accounts.length > 0) {
        selectAccount(accounts[0]);
      }
    } catch (err) {
      console.error(err);
      error = "Error checking connected accounts. Make sure your FastAPI backend is running.";
    } finally {
      loading = false;
    }
  }

  // 2. Fetch transactions for a selected account
  async function selectAccount(account) {
    selectedAccount = account;
    loadingTransactions = true;
    transactions = [];
    try {
      const id = account.id || account.accountId;
      const res = await fetch(`${BACKEND_URL}/transactions/${id}`);
      if (!res.ok) throw new Error("Could not retrieve transactions.");
      const data = await res.json();
      transactions = data.transactions || [];
    } catch (err) {
      console.error(err);
      error = "Error loading transactions for this account.";
    } finally {
      loadingTransactions = false;
    }
  }

  // 3. Start Connection Flow
  async function handleConnect() {
    isConnecting = true;
    statusMessage = "Starting Revolut connection...";
    try {
      const res = await fetch(`${BACKEND_URL}/revolut-session`);
      if (!res.ok) throw new Error("Failed to start session.");
      const data = await res.json();
      if (data.url) {
        statusMessage = "Redirecting you to Revolut securely...";
        window.location.href = data.url;
      } else {
        throw new Error("No authorization URL returned.");
      }
    } catch (err) {
      console.error(err);
      error = "Failed to start connection flow. Check your backend configurations.";
      isConnecting = false;
    }
  }

  // 4. Check on Mount for callback parameter '?code='
  onMount(async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
      isConnecting = true;
      statusMessage = "Connecting with Revolut. Exchanging credentials...";
      try {
        const res = await fetch(`${BACKEND_URL}/finalize?code=${code}`);
        if (!res.ok) throw new Error("Credentials exchange failed.");
        await res.json();
        
        statusMessage = "Account connected successfully!";
        
        // Curățare URL param discret
        const cleanUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
        window.history.replaceState({ path: cleanUrl }, '', cleanUrl);
      } catch (err) {
        console.error(err);
        error = "Failed to link card during callback exchange. Try again.";
      } finally {
        isConnecting = false;
      }
    }

    await loadAccounts();
  });

  // Helpers
  function getAmount(tx) {
    if (tx.transactionAmount) {
      return `${parseFloat(tx.transactionAmount.amount).toFixed(2)} ${tx.transactionAmount.currency}`;
    }
    if (tx.amount) {
      return `${parseFloat(tx.amount).toFixed(2)} ${tx.currency || ''}`;
    }
    return '0.00';
  }

  function getMerchant(tx) {
    if (tx.creditor && tx.creditor.name) return tx.creditor.name;
    if (tx.creditorName) return tx.creditorName;
    if (tx.remittanceInformation && tx.remittanceInformation[0]) return tx.remittanceInformation[0];
    if (tx.remittanceInformationUnstructured) return tx.remittanceInformationUnstructured;
    if (tx.description) return tx.description;
    return 'Unknown Merchant';
  }

  function getDate(tx) {
    const rawDate = tx.bookingDateTime || tx.bookingDate || tx.valueDate || tx.valueDateTime;
    if (!rawDate) return 'N/A';
    return new Date(rawDate).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function isSubscription(tx) {
    const merchant = getMerchant(tx).toLowerCase();
    const keywords = ['spotify', 'netflix', 'youtube', 'google', 'apple', 'amazon', 'adobe', 'microsoft', 'github', 'openai', 'chatgpt', 'patreon'];
    return keywords.some(kw => merchant.includes(kw));
  }
</script>

<div class="p-6 md:p-10 space-y-6">
  <!-- Top Navigation Bar -->
  <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-border">
    <div>
      <h1 class="text-3xl font-bold tracking-tight text-foreground">Dashboard Financiar</h1>
      <p class="text-sm text-muted-foreground">Monitorizează-ți conturile și tranzacțiile Revolut.</p>
    </div>
    <div class="flex items-center gap-3">
      <button 
        on:click={handleConnect}
        disabled={isConnecting}
        class="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50"
      >
        {isConnecting ? 'Se conectează...' : 'Conectează Revolut'}
      </button>
      
      <button 
        on:click={() => navigate('login')}
        class="bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border px-4 py-2 rounded-md font-medium text-sm transition-colors"
      >
        Ieși din cont
      </button>
    </div>
  </header>

  <!-- Status / Errors -->
  {#if error}
    <div class="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-lg text-sm">
      {error}
    </div>
  {:else if statusMessage}
    <div class="p-4 bg-primary/10 border border-primary/20 text-primary rounded-lg text-sm animate-pulse">
      {statusMessage}
    </div>
  {/if}

  <!-- Main Grid Layout -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
    
    <!-- Sidebar - Conturi Conectate -->
    <div class="md:col-span-1 space-y-4">
      <div class="bg-card text-card-foreground border border-border rounded-xl p-4">
        <h3 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Conturile Tale</h3>
        
        {#if loading}
          <div class="flex justify-center py-6">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
          </div>
        {:else if accounts.length === 0}
          <p class="text-xs text-muted-foreground text-center py-4">Niciun cont conectat încă.</p>
        {:else}
          <div class="space-y-2">
            {#each accounts as account}
              <button 
                on:click={() => selectAccount(account)}
                class="w-full text-left p-3 rounded-lg text-sm border transition-colors flex flex-col gap-1 
                {selectedAccount && (selectedAccount.id === account.id || selectedAccount.accountId === account.accountId)
                  ? 'bg-accent text-accent-foreground border-primary' 
                  : 'bg-background text-foreground border-border hover:bg-accent/50'}"
              >
                <span class="font-medium text-foreground">{account.name || 'Cont Revolut'}</span>
                <span class="text-xs text-muted-foreground">
                  {#if account.balance}
                    Balanță: {account.balance} {account.currency || ''}
                  {:else}
                    Selectează pentru detalii
                  {/if}
                </span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- Main Column - Istoric Tranzacții (Codul tău original) -->
    <div class="md:col-span-3">
      <div class="bg-card text-card-foreground border border-border rounded-xl overflow-hidden">
        <div class="p-6 border-b border-border flex justify-between items-center">
          <div>
            <h2 class="text-lg font-medium text-foreground">Istoric Tranzacții</h2>
            <p class="text-xs text-muted-foreground">Activitatea recentă a cardului selectat</p>
          </div>
          <span class="text-xs text-primary bg-primary/10 px-2.5 py-1 rounded-full border border-primary/20 font-medium">
            {transactions.length} Tranzacții Găsite
          </span>
        </div>

        {#if loadingTransactions}
          <div class="flex justify-center py-24">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        {:else if transactions.length === 0}
          <div class="text-center py-20 text-muted-foreground text-sm">
            Nu s-au găsit tranzacții pentru acest cont.
          </div>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-border text-xs text-muted-foreground bg-muted/50">
                  <th class="py-3.5 px-6 font-medium">Dată</th>
                  <th class="py-3.5 px-6 font-medium">Comerciant</th>
                  <th class="py-3.5 px-6 font-medium">Tip</th>
                  <th class="py-3.5 px-6 font-medium text-right">Sumă</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border text-sm text-foreground">
                {#each transactions as tx}
                  <tr class="hover:bg-muted/30 transition-colors">
                    <td class="py-4 px-6 text-xs text-muted-foreground whitespace-nowrap">
                      {getDate(tx)}
                    </td>
                    <td class="py-4 px-6 font-medium text-foreground">
                      <div class="flex items-center gap-2">
                        <span>{getMerchant(tx)}</span>
                        {#if isSubscription(tx)}
                          <span class="text-[9px] font-semibold text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded-full uppercase tracking-wider">
                            Sub Hint
                          </span>
                        {/if}
                      </div>
                    </td>
                    <td class="py-4 px-6 text-xs text-muted-foreground">
                      {isSubscription(tx) ? 'Abonament' : 'Cumpărături'}
                    </td>
                    <td class="py-4 px-6 text-right font-semibold text-foreground whitespace-nowrap">
                      {getAmount(tx)}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>
    
  </div>
</div>