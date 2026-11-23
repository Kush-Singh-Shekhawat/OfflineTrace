// @vitest-environment jsdom
import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from './App';
import * as api from '../shared/api';

vi.spyOn(api, 'fetchHealth').mockResolvedValue({ status: 'ok' });

describe('OfflineTrace App Shell', () => {
  it('renders dashboard, recipients, investigate, and ledger routes offline', () => {
    const routes = [
      { path: '/dashboard', heading: /Documents & Release/i },
      { path: '/recipients', heading: /Key & Recipient Management/i },
      { path: '/investigate', heading: /Forensic Investigation/i },
      { path: '/ledger', heading: /Quorum Ledger & Validator Nodes/i },
    ];

    for (const r of routes) {
      const { unmount } = render(
        <MemoryRouter initialEntries={[r.path]}>
          <AppRoutes />
        </MemoryRouter>
      );
      expect(screen.getByRole('heading', { name: r.heading })).toBeTruthy();
      unmount();
    }
  });
});
