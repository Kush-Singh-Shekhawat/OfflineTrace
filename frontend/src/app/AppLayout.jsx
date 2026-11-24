import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileLock, 
  Users, 
  SearchCheck, 
  Network, 
  ShieldCheck, 
  Radio, 
  Cpu, 
  Lock, 
  Terminal 
} from '../components/Icons.jsx';

export default function AppLayout() {
  const [tacticalTime, setTacticalTime] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const utcStr = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
      setTacticalTime(utcStr);
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: 'Tactical Dashboard', to: '/', icon: LayoutDashboard },
    { label: 'Document Packaging', to: '/documents', icon: FileLock },
    { label: 'Recipients & Keys', to: '/recipients', icon: Users },
    { label: 'Forensic Investigation', to: '/investigation', icon: SearchCheck },
    { label: 'Consensus Ledger', to: '/ledger', icon: Network },
  ];

  return (
    <div className="app-shell">
      {/* Tactical SOC Sidebar */}
      <aside className="sidebar">
        <div className="brand-header">
          <div className="brand-logo-glow">
            <ShieldCheck size={28} color="#00f0ff" />
          </div>
          <div>
            <div className="brand-title">OFFLINETRACE</div>
            <div className="brand-subtitle">WESEE // AIR-GAPPED SOC</div>
          </div>
        </div>

        <div className="security-tag-badge">
          <span className="security-dot-emerald"></span>
          <span>AIR-GAP ENCLAVE RESTRICTED</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink 
                key={item.to} 
                to={item.to} 
                end={item.to === '/'}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon size={18} className="nav-icon" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Hardware & Cryptographic Telemetry Panel */}
        <div className="telemetry-panel">
          <div className="telemetry-title">
            <Cpu size={13} color="#38bdf8" />
            <span>SYSTEM TELEMETRY</span>
          </div>
          <div className="telemetry-row">
            <span className="telemetry-label">SECURITY PROTOCOL</span>
            <span className="telemetry-value-cyan">NIST FIPS 203/204</span>
          </div>
          <div className="telemetry-row">
            <span className="telemetry-label">CONSENSUS STATE</span>
            <span className="telemetry-value-emerald">2-OF-3 QUORUM</span>
          </div>
          <div className="telemetry-row">
            <span className="telemetry-label">PERIMETER ISOLATION</span>
            <span className="telemetry-value-amber">PHYSICAL AIR-GAP</span>
          </div>
          <div className="telemetry-row">
            <span className="telemetry-label">MEMORY BOUNDARY</span>
            <span className="telemetry-value-emerald">ZERO-CUSTODY</span>
          </div>
        </div>

        <div className="sidebar-footer">
          <Radio size={12} className="pulse-beacon" />
          <span>OFFLINE LOCAL RUNTIME ACTIVE</span>
        </div>
      </aside>

      {/* Main Tactical Viewport */}
      <div className="content-container">
        {/* Top Tactical Ops Header */}
        <header className="ops-header">
          <div className="ops-left">
            <div className="ops-badge">
              <Lock size={12} color="#00f0ff" />
              <span>CLASSIFIED TACTICAL OPERATIONS</span>
            </div>
            <div className="ops-clock">
              <Terminal size={12} color="#94a3b8" />
              <span>{tacticalTime || 'INITIALIZING CLOCK...'}</span>
            </div>
          </div>
          
          <div className="ops-right">
            <div className="crypto-badge">
              <span className="crypto-dot-cyan"></span>
              <span>ML-KEM-768 // ML-DSA-65</span>
            </div>
            <div className="status-pill-emerald">
              <span className="pulse-dot"></span>
              <span>LAN SECURED &bull; WAN DISCONNECTED</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
