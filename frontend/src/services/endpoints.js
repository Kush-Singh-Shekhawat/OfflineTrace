import { apiRequest } from './apiClient.js';

export const getHealth = () => apiRequest('/health');
export const getDashboardSummary = () => apiRequest('/api/v1/dashboard/summary');
export const getLedgerStatus = () => apiRequest('/api/v1/ledger/status');
