import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    }
});

export const finalizeSession = async (code) => {
    const response = await api.get(`/finalize?code=${code}`);
    return response.data;
};

export const getTransactions = async (accountUid) => {
    const response = await api.get(`/transactions/${accountUid}`);
    // Enable Banking usually returns { transactions: [...] }
    return response.data.transactions || [];
};
