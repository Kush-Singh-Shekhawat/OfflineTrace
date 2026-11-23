import React, { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from '../shared/Layout';
import { fetchHealth } from '../shared/api';

export const DashboardPage: React.FC = () => (
  <div>
    <h1 className="text-xl font-semibold">Documents & Release</h1>
    <p className="text-slate-400 text-sm mt-1">
      Protected document sealing and recipient distribution workspace.
    </p>
  </div>
);

export const RecipientsPlaceholder: React.FC = () => (
  <div>
    <h1 className="text-xl font-semibold">Key & Recipient Management</h1>
    <p className="text-slate-400 text-sm mt-1">Member A module slot.</p>
  </div>
);

export const InvestigatePlaceholder: React.FC = () => (
  <div>
    <h1 className="text-xl font-semibold">Forensic Investigation</h1>
    <p className="text-slate-400 text-sm mt-1">Member B module slot.</p>
  </div>
);

export const LedgerPage: React.FC = () => (
  <div>
    <h1 className="text-xl font-semibold">Quorum Ledger & Validator Nodes</h1>
    <p className="text-slate-400 text-sm mt-1">
      2-of-3 consensus chain height and block verification view.
    </p>
  </div>
);

export const AppRoutes: React.FC = () => {
  const [online, setOnline] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
  }, []);

  return (
    <Layout backendOnline={online}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/recipients" element={<RecipientsPlaceholder />} />
        <Route path="/investigate" element={<InvestigatePlaceholder />} />
        <Route path="/ledger" element={<LedgerPage />} />
      </Routes>
    </Layout>
  );
};

export const App: React.FC = () => (
  <BrowserRouter>
    <AppRoutes />
  </BrowserRouter>
);

export default App;
