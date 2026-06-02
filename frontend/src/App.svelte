<script>
  import { onMount } from 'svelte';

  let accounts = [];
  let selectedAccount = null;
  let transactions = [];
  let loading = true;
  let isConnecting = false;
  let loadingTransactions = false;
  let error = null;
  let statusMessage = "";

  // FastAPI backend base URL
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
      
      // Auto-select the first account if found
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
        // Direct browser redirect
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
        
        // Remove the '?code=...' query parameter from the URL bar cleanly
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

  // Helpers to safely parse bank transaction properties
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
    return new Date(rawDate).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  // Pre-emptive subscription detection matching logic
  function isSubscription(tx) {
    const merchant = getMerchant(tx).toLowerCase();
    const keywords = ['spotify', 'netflix', 'youtube', 'google', 'apple', 'amazon', 'adobe', 'microsoft', 'github', 'openai', 'chatgpt', 'patreon'];
    return keywords.some(kw => merchant.includes(kw));
  }
</script>

<main class="min-h-screen bg-slate-950 text-slate-50 font-sans antialiased">
  <!-- Top Navigation Header -->
  <header class="border-b border-slate-800 bg-slate-900/40 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="h-6 w-6 rounded bg-indigo-600 flex items-center justify-center font-bold text-xs">CW</div>
        <span class="font-semibold text-lg tracking-tight">CostWatch</span>
      </div>
      <div>
        <button 
          on:click={handleConnect} 
          disabled={isConnecting}
          class="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors shadow disabled:opacity-50"
        >
          {isConnecting ? 'Connecting...' : 'Connect Revolut'}
        </button>
      </div>
    </div>
  </header>

  <!-- Notification Banner -->
  {#if statusMessage || error}
    <div class="max-w-7xl mx-auto px-6 pt-4">
      {#if error}
        <div class="p-4 rounded-lg bg-red-950/40 border border-red-900 text-red-200 text-sm">
          {error}
        </div>
      {:else if statusMessage}
        <div class="p-4 rounded-lg bg-indigo-950/40 border border-indigo-900 text-indigo-200 text-sm flex items-center gap-3">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
          </span>
          {statusMessage}
        </div>
      {/if}
    </div>
  {/if}

  <div class="max-w-7xl mx-auto px-6 py-8">
    {#if loading}
      <div class="flex items-center justify-center py-20">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    {:else if accounts.length === 0}
      <!-- Empty State -->
      <div class="text-center py-20 max-w-md mx-auto">
        <div class="h-12 w-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-slate-400">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
          </svg>
        </div>
        <h3 class="text-lg font-medium text-slate-200">No bank account connected</h3>
        <p class="text-sm text-slate-400 mt-2 mb-6">
          Connect your Revolut account to analyze your transactions, identify hidden subscriptions, and route updates to Discord.
        </p>
        <button 
          on:click={handleConnect} 
          class="px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-md border border-slate-700 transition-all"
        >
          Link Revolut Card
        </button>
      </div>
    {:else}
      <!-- Active Dashboard layout -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <!-- Sidebar - Accounts panel -->
        <div class="md:col-span-1 space-y-4">
          <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">Your Connected Cards</h2>
          <div class="space-y-2">
            {#each accounts as account}
              <button 
                on:click={() => selectAccount(account)}
                class="w-full text-left p-4 rounded-xl border transition-all relative overflow-hidden group
                  {selectedAccount?.id === account.id || selectedAccount?.accountId === account.accountId
                    ? 'bg-slate-900 border-indigo-500 shadow-md shadow-indigo-950/20' 
                    : 'bg-slate-950 border-slate-800 hover:bg-slate-900/50 hover:border-slate-700'}"
              >
                <div class="flex justify-between items-start mb-2">
                  <span class="text-xs font-medium text-indigo-400">Revolut</span>
                  <span class="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">RO</span>
                </div>
                <div class="text-xl font-semibold tracking-tight text-slate-100">
                  {account.balances?.[0]?.balanceAmount?.amount || '***'} 
                  <span class="text-sm text-slate-400">{account.currency || ''}</span>
                </div>
                <div class="text-[11px] text-slate-500 mt-3 truncate">
                  IBAN: {account.identifications?.[0]?.identification || 'N/A'}
                </div>
              </button>
            {/each}
          </div>
        </div>

        <!-- Main Column - Transaction Details -->
        <div class="md:col-span-3">
          <div class="bg-slate-900/20 border border-slate-800 rounded-xl overflow-hidden">
            <div class="p-6 border-b border-slate-800 flex justify-between items-center">
              <div>
                <h2 class="text-lg font-medium text-slate-100">Transaction History</h2>
                <p class="text-xs text-slate-400">Showing recent activity for the selected card</p>
              </div>
              <span class="text-xs text-indigo-400 bg-indigo-950/30 px-2.5 py-1 rounded-full border border-indigo-900/40 font-medium">
                {transactions.length} Records Found
              </span>
            </div>

            {#if loadingTransactions}
              <div class="flex justify-center py-24">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
              </div>
            {:else if transactions.length === 0}
              <div class="text-center py-20 text-slate-500 text-sm">
                No transactions found for this account.
              </div>
            {:else}
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="border-b border-slate-800 text-xs text-slate-400 bg-slate-900/10">
                      <th class="py-3.5 px-6 font-medium">Date</th>
                      <th class="py-3.5 px-6 font-medium">Merchant</th>
                      <th class="py-3.5 px-6 font-medium">Type</th>
                      <th class="py-3.5 px-6 font-medium text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-800/60 text-sm text-slate-300">
                    {#each transactions as tx}
                      <tr class="hover:bg-slate-900/20 transition-colors">
                        <td class="py-4 px-6 text-xs text-slate-500 whitespace-nowrap">
                          {getDate(tx)}
                        </td>
                        <td class="py-4 px-6 font-medium text-slate-200">
                          <div class="flex items-center gap-2">
                            <span>{getMerchant(tx)}</span>
                            {#if isSubscription(tx)}
                              <span class="text-[9px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-900 px-1.5 py-0.5 rounded-full uppercase tracking-wider">
                                Sub Hint
                              </span>
                            {/if}
                          </div>
                        </td>
                        <td class="py-4 px-6 text-xs text-slate-400">
                          {isSubscription(tx) ? 'Subscription' : 'Purchase'}
                        </td>
                        <td class="py-4 px-6 text-right font-semibold text-slate-200 whitespace-nowrap">
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
    {/if}
  </div>
</main>