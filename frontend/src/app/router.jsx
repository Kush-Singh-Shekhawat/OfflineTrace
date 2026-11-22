import { createBrowserRouter } from 'react-router-dom';
import AppLayout from './AppLayout.jsx';
import DashboardPage from '../features/dashboard/DashboardPage.jsx';
import DocumentsPage from '../features/documents/DocumentsPage.jsx';
import RecipientsPage from '../features/recipients/RecipientsPage.jsx';
import InvestigationPage from '../features/investigation/InvestigationPage.jsx';
import LedgerPage from '../features/ledger/LedgerPage.jsx';

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <DashboardPage /> },
      { path: '/documents', element: <DocumentsPage /> },
      { path: '/recipients', element: <RecipientsPage /> },
      { path: '/investigation', element: <InvestigationPage /> },
      { path: '/ledger', element: <LedgerPage /> },
    ],
  },
]);
