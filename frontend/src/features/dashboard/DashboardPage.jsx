import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../services/apiClient.js';

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadSummary() {
      try {
        setLoading(true);
        const data = await apiRequest('/api/v1/dashboard/summary');
        setSummary(data);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard metrics.');
      } finally {
        setLoading(false);
      }
    }
    loadSummary();
  }, []);

  return (
    <section style={{ maxWidth: '1080px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', margin: '0 0 6px 0', color: '#0f172a' }}>
          OfflineTrace &mdash; System Command Dashboard
        </h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: '0.95rem' }}>
          Ministry of Defence / WESEE (SIH26237) &bull; Controlled Document Distribution &amp; Post-Quantum Forensic Attribution.
        </p>
      </header>

      {/* Military Operations Status Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: '#ffffff',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div>
          <div style={{
            display: 'inline-block',
            background: '#059669',
            color: '#ffffff',
            fontSize: '0.72rem',
            fontWeight: 800,
            padding: '2px 8px',
            borderRadius: '4px',
            letterSpacing: '0.08em',
            marginBottom: '8px',
          }}>
            SYSTEM ACTIVE &bull; WAN DISCONNECTED OPERATIONAL
          </div>
          <h3 style={{ margin: '0 0 6px 0', fontSize: '1.3rem', color: '#f8fafc' }}>
            Air-Gapped Tactical Security Network
          </h3>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8', maxWidth: '600px', lineHeight: 1.5 }}>
            OfflineTrace operates across isolated local networks. All document distributions enforce 
            <strong> NIST FIPS 203 ML-KEM-768</strong> key encapsulation, 
            <strong> NIST FIPS 204 ML-DSA-65</strong> provenance signatures, and 
            <strong> 2-of-3 Byzantine Quorum</strong> consensus before document release.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Consensus Mode</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399', marginTop: '2px' }}>
            2-of-3 Quorum Active
          </div>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '4px' }}>
            Nodes: val-1, val-2, val-3
          </div>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '24px',
          color: '#991b1b',
          fontSize: '0.9rem',
        }}>
          <strong>Notice:</strong> {error}
        </div>
      )}

      {/* 4 Executive Metric Counters */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '32px',
      }}>
        <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>PROTECTED DIRECTIVES</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', margin: '6px 0' }}>
            {summary ? summary.documents_total : '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#0284c7' }}>
            AES-256-GCM + PQC Envelopes
          </div>
        </div>

        <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>ENROLLED OFFICERS</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', margin: '6px 0' }}>
            {summary ? summary.recipients_total : '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#15803d' }}>
            ML-KEM-768 &amp; ML-DSA-65 Keys
          </div>
        </div>

        <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>COMMITTED BLOCKS</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', margin: '6px 0' }}>
            {summary ? summary.chain_height : '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#7c3aed' }}>
            Immutable SHA3-256 Hash Chain
          </div>
        </div>

        <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b' }}>FORENSIC INQUIRIES</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', margin: '6px 0' }}>
            {summary ? summary.investigations_total : '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#ea580c' }}>
            Cryptographically Sealed Dossiers
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <h3 style={{ fontSize: '1.15rem', color: '#1e293b', marginBottom: '16px' }}>
        🚀 Workflow Navigation
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        <Link
          to="/documents"
          style={{
            textDecoration: 'none',
            background: '#ffffff',
            padding: '20px',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            display: 'block',
          }}
        >
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>📁</div>
          <strong style={{ color: '#0f172a', fontSize: '1rem', display: 'block', marginBottom: '4px' }}>
            Protect &amp; Distribute
          </strong>
          <span style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.4, display: 'block' }}>
            Encrypt classified PDFs with AES-256-GCM and generate recipient ML-KEM-768 envelopes.
          </span>
        </Link>

        <Link
          to="/recipients"
          style={{
            textDecoration: 'none',
            background: '#ffffff',
            padding: '20px',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            display: 'block',
          }}
        >
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>👤</div>
          <strong style={{ color: '#0f172a', fontSize: '1rem', display: 'block', marginBottom: '4px' }}>
            Officer Key Roster &amp; Tamper Tests
          </strong>
          <span style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.4, display: 'block' }}>
            Manage post-quantum keypairs, execute local decrypts, and test adversarial tamper attacks.
          </span>
        </Link>

        <Link
          to="/investigation"
          style={{
            textDecoration: 'none',
            background: '#ffffff',
            padding: '20px',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            display: 'block',
          }}
        >
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🔍</div>
          <strong style={{ color: '#0f172a', fontSize: '1rem', display: 'block', marginBottom: '4px' }}>
            Forensic Investigation
          </strong>
          <span style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.4, display: 'block' }}>
            Analyze suspected leaked PDFs, extract forensic watermarks, and generate Court of Inquiry dossiers.
          </span>
        </Link>

        <Link
          to="/ledger"
          style={{
            textDecoration: 'none',
            background: '#ffffff',
            padding: '20px',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
            display: 'block',
          }}
        >
          <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>⛓️</div>
          <strong style={{ color: '#0f172a', fontSize: '1rem', display: 'block', marginBottom: '4px' }}>
            Ledger &amp; Consensus Explorer
          </strong>
          <span style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.4, display: 'block' }}>
            Inspect committed blocks, 2-of-3 quorum validator signatures, and SHA3-256 hash chains.
          </span>
        </Link>
      </div>
    </section>
  );
}
