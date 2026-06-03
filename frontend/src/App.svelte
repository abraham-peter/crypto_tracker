<script>
  import { onMount } from 'svelte';

  let accounts = [];
  let selectedAccount = null;
  let transactions = [];
  
  let loading = true;
  let isConnecting = false;
  let loadingTransactions = false;
  let isSyncing = false;
  
  let error = null;
  let statusMessage = "";

  // Filtre
  let searchQuery = "";
  let selectedCategory = "";

  const BACKEND_URL = "http://127.0.0.1:8000";

  // Încărcare conturi salvate în baza de date locală
  async function loadAccounts() {
    loading = true;
    error = null;
    try {
      const res = await fetch(`${BACKEND_URL}/accounts`);
      if (!res.ok) throw new Error("Nu s-au putut încărca conturile.");
      const data = await res.json();
      accounts = data.accounts || [];
      
      if (accounts.length > 0) {
        // Păstrează contul selectat anterior dacă există, altfel primul din listă
        if (!selectedAccount) {
          selectAccount(accounts[0]);
        } else {
          selectAccount(selectedAccount);
        }
      }
    } catch (err) {
      console.error(err);
      error = "Eroare la conexiunea cu serverul backend.";
    } finally {
      loading = false;
    }
  }

  // Încărcare tranzacții din DB locală cu query params pentru filtre
  async function selectAccount(account) {
    selectedAccount = account;
    loadingTransactions = true;
    try {
      const id = account.id;
      // Construim URL-ul cu parametrii de căutare și filtrare
      let url = `${BACKEND_URL}/transactions/${id}?`;
      if (searchQuery) url += `search=${encodeURIComponent(searchQuery)}&`;
      if (selectedCategory) url += `category=${encodeURIComponent(selectedCategory)}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error("Nu s-au putut prelua tranzacțiile.");
      const data = await res.json();
      transactions = data.transactions || [];
    } catch (err) {
      console.error(err);
      error = "Eroare la încărcarea tranzacțiilor.";
    } finally {
      loadingTransactions = false;
    }
  }

  // Trigger pentru apelul backend de sincronizare cu Revolut API
  async function syncWithBank() {
    isSyncing = true;
    statusMessage = "Se descarcă tranzacțiile recente de la Revolut...";
    try {
      const res = await fetch(`${BACKEND_URL}/sync`, { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        statusMessage = "Sincronizare finalizată cu succes!";
        await loadAccounts(); // Reîncărcăm datele proaspăt salvate în DB
      } else {
        throw new Error(data.message);
      }
    } catch (err) {
      console.error(err);
      error = "Eroare la sincronizarea cu Revolut API.";
    } finally {
      isSyncing = false;
      // Curăță mesajul după 4 secunde
      setTimeout(() => { statusMessage = ""; }, 4000);
    }
  }

  async function handleConnect() {
    isConnecting = true;
    statusMessage = "Se inițializează conexiunea Revolut...";
    try {
      const res = await fetch(`${BACKEND_URL}/revolut-session`);
      if (!res.ok) throw new Error("Eroare la pornirea sesiunii.");
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error("Nu s-a primit un URL de autorizare.");
      }
    } catch (err) {
      console.error(err);
      error = "Eroare la redirecționare.";
      isConnecting = false;
    }
  }

  // Reactivitate: când se modifică bara de căutare sau categoria selectată, reîncărcăm tranzacțiile contului curent
  $: if (selectedAccount !== null && (searchQuery !== undefined || selectedCategory !== undefined)) {
    // Adăugăm un mic debounce opțional în mod normal, dar merge perfect și direct pe evenimente de input
    selectAccount(selectedAccount);
  }

  onMount(async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
      isConnecting = true;
      statusMessage = "Se validează conexiunea cu banca...";
      try {
        const res = await fetch(`${BACKEND_URL}/finalize?code=${code}`);
        if (!res.ok) throw new Error("Validare eșuată.");
        await res.json();
        
        statusMessage = "Card Revolut conectat cu succes! Se efectuează prima sincronizare...";
        
        // Șterge parametrul '?code=' din URL fără reîncărcare de pagină
        const cleanUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
        window.history.replaceState({ path: cleanUrl }, '', cleanUrl);
        
        // Pornește prima sincronizare automată în baza de date
        await syncWithBank();
      } catch (err) {
        console.error(err);
        error = "Eroare la finalizarea legăturii cu banca.";
      } finally {
        isConnecting = false;
      }
    } else {
      await loadAccounts();
    }
  });

  // Formatori frontend simpli
  function formatDate(isoString) {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
</script>

<main class="min-h-screen bg-slate-950 text-slate-50 font-sans antialiased">
  <!-- Navigarea de sus -->
  <header class="border-b border-slate-800 bg-slate-900/40 backdrop-blur-md sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="h-6 w-6 rounded bg-indigo-600 flex items-center justify-center font-bold text-xs">CW</div>
        <span class="font-semibold text-lg tracking-tight">CostWatch</span>
      </div>
      <div class="flex items-center gap-3">
        {#if accounts.length > 0}
          <button 
            on:click={syncWithBank} 
            disabled={isSyncing}
            class="px-4 py-2 text-sm font-medium bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 rounded-md transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {#if isSyncing}
              <span class="animate-spin h-3.5 w-3.5 border-2 border-indigo-500 border-t-transparent rounded-full"></span>
              Sincronizare...
            {:else}
              <span>Sincronizează datele</span>
            {/if}
          </button>
        {/if}
        <button 
          on:click={handleConnect} 
          disabled={isConnecting}
          class="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors shadow disabled:opacity-50"
        >
          {isConnecting ? 'Se conectează...' : 'Conectează Revolut'}
        </button>
      </div>
    </div>
  </header>

  <!-- Status / Erori -->
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
        <h3 class="text-lg font-medium text-slate-200">Nu ai niciun cont conectat</h3>
        <p class="text-sm text-slate-400 mt-2 mb-6">
          Conectează-ți contul de Revolut pentru a-ți stoca tranzacțiile local, a detecta automat abonamentele active și a primi alerte pe Discord.
        </p>
        <button 
          on:click={handleConnect} 
          class="px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-md border border-slate-700 transition-all"
        >
          Adaugă Revolut local
        </button>
      </div>
    {:else}
      <!-- Layout Principal Dashboard -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        
        <!-- Sidebar - Conturi salvate local -->
        <div class="md:col-span-1 space-y-4">
          <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">Conturi Salvate local</h2>
          <div class="space-y-2">
            {#each accounts as account}
              <button 
                on:click={() => selectAccount(account)}
                class="w-full text-left p-4 rounded-xl border transition-all relative overflow-hidden group
                  {selectedAccount?.id === account.id
                    ? 'bg-slate-900 border-indigo-500 shadow-md shadow-indigo-950/20' 
                    : 'bg-slate-950 border-slate-800 hover:bg-slate-900/50 hover:border-slate-700'}"
              >
                <div class="flex justify-between items-start mb-2">
                  <span class="text-xs font-medium text-indigo-400">{account.name}</span>
                  <span class="text-[10px] bg-indigo-950/30 px-1.5 py-0.5 rounded text-indigo-300 border border-indigo-900/30">Local DB</span>
                </div>
                <div class="text-xl font-semibold tracking-tight text-slate-100">
                  {account.balance.toFixed(2)} 
                  <span class="text-sm text-slate-400">{account.currency}</span>
                </div>
                <div class="text-[11px] text-slate-500 mt-3 truncate">
                  IBAN: {account.id}
                </div>
              </button>
            {/each}
          </div>
        </div>

        <!-- Istoric Tranzacții cu filtre de Căutare -->
        <div class="md:col-span-3 space-y-4">
          
          <!-- Bara de filtre -->
          <div class="bg-slate-900/30 border border-slate-800 p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center">
            
            <!-- Căutare după nume -->
            <div class="relative w-full md:flex-1">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-slate-400">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.637 10.637z" />
                </svg>
              </span>
              <input 
                type="text" 
                placeholder="Caută după comerciant (ex: Netflix, Lidl...)" 
                bind:value={searchQuery}
                class="w-full bg-slate-950 text-sm text-slate-200 pl-10 pr-4 py-2 border border-slate-800 rounded-lg focus:outline-none focus:border-indigo-500 placeholder-slate-500 transition-colors"
              />
            </div>

            <!-- Filtru după categorie -->
            <div class="w-full md:w-48">
              <select 
                bind:value={selectedCategory}
                class="w-full bg-slate-950 text-sm text-slate-200 px-3 py-2 border border-slate-800 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
              >
                <option value="">Toate Categoriile</option>
                <option value="Abonament">Abonamente</option>
                <option value="Groceries">Cumpărături / Groceries</option>
                <option value="Mâncare & Restaurant">Mâncare & Restaurant</option>
                <option value="Transport & Auto">Transport & Auto</option>
                <option value="Utilități">Utilități</option>
                <option value="Altele">Altele</option>
              </select>
            </div>
          </div>

          <!-- Tabelul de tranzacții -->
          <div class="bg-slate-900/20 border border-slate-800 rounded-xl overflow-hidden">
            <div class="p-6 border-b border-slate-800 flex justify-between items-center">
              <div>
                <h2 class="text-lg font-medium text-slate-100">Registru Tranzacții</h2>
                <p class="text-xs text-slate-400">Date securizate local, actualizate din DB.</p>
              </div>
              <span class="text-xs text-indigo-400 bg-indigo-950/30 px-2.5 py-1 rounded-full border border-indigo-900/40 font-medium">
                {transactions.length} înregistrări găsite
              </span>
            </div>

            {#if loadingTransactions}
              <div class="flex justify-center py-24">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
              </div>
            {:else if transactions.length === 0}
              <div class="text-center py-20 text-slate-500 text-sm">
                Nu s-au găsit rezultate conform filtrelor selectate.
              </div>
            {:else}
              <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="border-b border-slate-800 text-xs text-slate-400 bg-slate-900/10">
                      <th class="py-3.5 px-6 font-medium">Dată</th>
                      <th class="py-3.5 px-6 font-medium">Comerciant</th>
                      <th class="py-3.5 px-6 font-medium">Categorie</th>
                      <th class="py-3.5 px-6 font-medium text-right">Sumă</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-800/60 text-sm text-slate-300">
                    {#each transactions as tx}
                      <tr class="hover:bg-slate-900/20 transition-colors">
                        <td class="py-4 px-6 text-xs text-slate-500 whitespace-nowrap">
                          {formatDate(tx.booking_date)}
                        </td>
                        <td class="py-4 px-6 font-medium text-slate-200">
                          {tx.merchant}
                        </td>
                        <td class="py-4 px-6">
                          <span class="text-[10px] font-semibold px-2 py-1 rounded-md border 
                            {tx.category === 'Abonament' ? 'text-emerald-400 bg-emerald-950/40 border-emerald-900/50' : ''}
                            {tx.category === 'Groceries' ? 'text-blue-400 bg-blue-950/40 border-blue-900/50' : ''}
                            {tx.category === 'Mâncare & Restaurant' ? 'text-amber-400 bg-amber-950/40 border-amber-900/50' : ''}
                            {tx.category === 'Transport & Auto' ? 'text-cyan-400 bg-cyan-950/40 border-cyan-900/50' : ''}
                            {tx.category === 'Utilități' ? 'text-purple-400 bg-purple-950/40 border-purple-900/50' : ''}
                            {tx.category === 'Altele' ? 'text-slate-400 bg-slate-900/40 border-slate-800' : ''}
                          ">
                            {tx.category}
                          </span>
                        </td>
                        <td class="py-4 px-6 text-right font-semibold text-slate-200 whitespace-nowrap">
                          {tx.amount.toFixed(2)} {tx.currency}
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