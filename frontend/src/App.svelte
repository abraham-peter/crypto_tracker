<script lang="ts">
  import * as Table from "$lib/components/ui/table/index.js";
  import { onMount } from 'svelte';
  import { getTransactions, finalizeSession } from './api/transactions.js';

  let transactions = [];
  let isLoading = true;
  let error = null;

  onMount(async () => {
    // 1. Check the URL for the 'code' query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
      isLoading = true;
      try {
        // 2. Finalize the session to get account details
        const sessionResult = await finalizeSession(code);
        
        // Ensure your backend returns the accounts array
        // We usually take the first account available
        const accountUid = sessionResult.accounts?.[0]?.uid;

        if (accountUid) {
          // 3. Fetch the actual history
          const data = await getTransactions(accountUid);
          transactions = data.transactions || [];
        } else {
          error = "No accounts linked to this session.";
        }
      } catch (err) {
        error = "Failed to synchronize with the bank.";
        console.error(err);
      } finally {
        isLoading = false;
      }
    }
  });
  $: totalAmount = transactions.reduce((acc, tx) => {
    return acc + parseFloat(tx.transaction_amount?.amount || 0);
  }, 0);

</script>

<Table.Root>
  <Table.Caption>A list of your recent transactions.</Table.Caption>
  <Table.Header>
    <Table.Row>
      <Table.Head>Date</Table.Head>
      <Table.Head>Description</Table.Head>
      <Table.Head>Status</Table.Head>
      <Table.Head class="text-end">Amount</Table.Head>
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {#if isLoading}
      <Table.Row><Table.Cell colspan={4}>Loading...</Table.Cell></Table.Row>
    {:else if error}
      <Table.Row><Table.Cell colspan={4} class="text-red-500">{error}</Table.Cell></Table.Row>
    {:else}
      {#each transactions as tx}
        <Table.Row>
          <Table.Cell>{tx.booking_date || tx.value_date}</Table.Cell>
          <Table.Cell>{tx.remittance_information_unstructured || 'No description'}</Table.Cell>
          <Table.Cell>{tx.status || 'Booked'}</Table.Cell>
          <Table.Cell class="text-end">
            {tx.transaction_amount.amount} {tx.transaction_amount.currency}
          </Table.Cell>
        </Table.Row>
      {/each}
    {/if}
  </Table.Body>
</Table.Root>