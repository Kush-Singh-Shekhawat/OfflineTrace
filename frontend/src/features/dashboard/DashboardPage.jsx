import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../services/apiClient.js';
import { 
  ShieldCheck, 
  FileLock, 
  Users, 
  SearchCheck, 
  Network, 
  Radio, 
  ArrowRight, 
  Database, 
  Lock, 
  Cpu 
} from '../../components/Icons.jsx';

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
    <section style={{ maxWidth: '1180px', margin: '0 auto', fontFamily: 'inherit' }}>
      {/* Page Header */}
      <header style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#00f0ff',
              boxShadow: '0 0 10px #00f0ff'
            }} />
            <h2 style={{ fontSize: '1.85rem', margin: 0, color: '#ffffff', fontWeight: 800, letterSpacing: '0.04em' }}>
              TACTICAL OPERATIONS COMMAND
            </h2>
          </div>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.92rem' }}>
            Ministry of Defence / WESEE (SIH26237) &bull; Air-Gapped Controlled Document Distribution &amp; Post-Quantum Attribution
          </p>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(0, 240, 255, 0.08)',
          border: '1px solid rgba(0, 240, 255, 0.25)',
          padding: '8px 14px',
          borderRadius: '8px',
          fontSize: '0.78rem',
          color: '#38bdf8',
          fontFamily: 'var(--font-mono)'
        }}>
          <Radio size={14} className="pulse-beacon" />
          <span>SECURITY DOMAIN: RESTRICTED ENCLAVE</span>
        </div>
      </header>

      {/* Cyber Military Status Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(9, 14, 26, 0.95) 100%)',
        border: '1px solid rgba(0, 240, 255, 0.25)',
        borderRadius: '14px',
        padding: '26px 28px',
        marginBottom: '28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
        flexWrap: 'wrap',
        gap: '20px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ maxWidth: '640px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            color: '#34d399',
            fontSize: '0.72rem',
            fontWeight: 800,
            padding: '3px 10px',
            borderRadius: '4px',
            letterSpacing: '0.1em',
            marginBottom: '12px',
            fontFamily: 'var(--font-mono)'
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
            AIR-GAPPED DEFENCE PROTOCOL
          </div>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1.25rem', color: '#ffffff', fontWeight: 700 }}>
            Post-Quantum Sovereign Cryptographic Network
          </h3>
          <p style={{ margin: 0, fontSize: '0.88rem', color: '#94a3b8', lineHeight: 1.6 }}>
            Operating strictly across local air-gapped physical interfaces. Documents are sealed with 
            <strong style={{ color: '#38bdf8' }}> NIST FIPS 203 ML-KEM-768</strong> multi-recipient envelopes, 
            watermarked with forensic redundancy, and signed with 
            <strong style={{ color: '#34d399' }}> NIST FIPS 204 ML-DSA-65</strong> before 
            <strong style={{ color: '#fbbf24' }}> 2-of-3 Byzantine Quorum</strong> consensus release.
          </p>
        </div>

        <div style={{
          background: 'rgba(6, 11, 22, 0.8)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '10px',
          padding: '16px 20px',
          minWidth: '220px',
          textAlign: 'right'
        }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'var(--font-mono)', letterSpacing: '0.08em' }}>
            CLUSTER CONSENSUS
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#34d399', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
            2-of-3 QUORUM
          </div>
          <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
            ACTIVE: val-1 &bull; val-2 &bull; val-3
          </div>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '10px',
          padding: '14px 18px',
          marginBottom: '24px',
          color: '#fca5a5',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontWeight: 800, color: '#ef4444' }}>ALERT:</span> {error}
        </div>
      )}

      {/* 4 Executive Metric Counters */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '18px',
        marginBottom: '36px',
      }}>
        {/* Metric 1 */}
        <div style={{
          background: 'rgba(13, 20, 36, 0.85)',
          padding: '22px 24px',
          borderRadius: '12px',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)' }}>
              PROTECTED DIRECTIVES
            </span>
            <FileLock size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', margin: '8px 0', fontFamily: 'var(--font-mono)' }}>
            {summary ? summary.documents_total : (loading ? '...' : '0')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
            AES-256-GCM + PQC Envelopes
          </div>
        </div>

        {/* Metric 2 */}
        <div style={{
          background: 'rgba(13, 20, 36, 0.85)',
          padding: '22px 24px',
          borderRadius: '12px',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)' }}>
              ENROLLED OFFICERS
            </span>
            <Users size={18} color="#34d399" />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', margin: '8px 0', fontFamily: 'var(--font-mono)' }}>
            {summary ? summary.recipients_total : (loading ? '...' : '0')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#34d399', fontFamily: 'var(--font-mono)' }}>
            ML-KEM-768 &amp; ML-DSA-65 Keys
          </div>
        </div>

        {/* Metric 3 */}
        <div style={{
          background: 'rgba(13, 20, 36, 0.85)',
          padding: '22px 24px',
          borderRadius: '12px',
          border: '1px solid rgba(168, 85, 247, 0.25)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)' }}>
              COMMITTED BLOCKS
            </span>
            <Network size={18} color="#c084fc" />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', margin: '8px 0', fontFamily: 'var(--font-mono)' }}>
            {summary ? summary.chain_height : (loading ? '...' : '0')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#c084fc', fontFamily: 'var(--font-mono)' }}>
            Immutable SHA3-256 Hash Chain
          </div>
        </div>

        {/* Metric 4 */}
        <div style={{
          background: 'rgba(13, 20, 36, 0.85)',
          padding: '22px 24px',
          borderRadius: '12px',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#94a3b8', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)' }}>
              FORENSIC INQUIRIES
            </span>
            <SearchCheck size={18} color="#fbbf24" />
          </div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', margin: '8px 0', fontFamily: 'var(--font-mono)' }}>
            {summary ? summary.investigations_total : (loading ? '...' : '0')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#fbbf24', fontFamily: 'var(--font-mono)' }}>
            Cryptographically Sealed Dossiers
          </div>
        </div>
      </div>

      {/* Cyber Operations Workflow Matrix */}
      <h3 style={{ fontSize: '1.1rem', color: '#e2e8f0', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', letterSpacing: '0.04em' }}>
        <Cpu size={16} color="#00f0ff" />
        TACTICAL OPERATIONS MATRIX
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px' }}>
        {/* Card 1 */}
        <Link
          to="/documents"
          style={{
            textDecoration: 'none',
            background: 'rgba(13, 20, 36, 0.75)',
            padding: '22px',
            borderRadius: '12px',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            transition: 'all 0.2s ease',
            display: 'block'
          }}
          className="cyber-hover-card"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileLock size={20} color="#38bdf8" />
            </div>
            <ArrowRight size={16} color="#64748b" />
          </div>
          <strong style={{ color: '#ffffff', fontSize: '1.05rem', display: 'block', marginBottom: '6px' }}>
            Protect &amp; Distribute
          </strong>
          <span style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, display: 'block' }}>
            Encrypt classified PDFs with AES-256-GCM and generate recipient-specific ML-KEM-768 envelopes.
          </span>
        </Link>

        {/* Card 2 */}
        <Link
          to="/recipients"
          style={{
            textDecoration: 'none',
            background: 'rgba(13, 20, 36, 0.75)',
            padding: '22px',
            borderRadius: '12px',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            transition: 'all 0.2s ease',
            display: 'block'
          }}
          className="cyber-hover-card"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Users size={20} color="#34d399" />
            </div>
            <ArrowRight size={16} color="#64748b" />
          </div>
          <strong style={{ color: '#ffffff', fontSize: '1.05rem', display: 'block', marginBottom: '6px' }}>
            Officer Key Roster &amp; Tamper Tests
          </strong>
          <span style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, display: 'block' }}>
            Manage post-quantum keypairs, simulate local decrypts, and test 7 adversarial tamper attacks.
          </span>
        </Link>

        {/* Card 3 */}
        <Link
          to="/investigation"
          style={{
            textDecoration: 'none',
            background: 'rgba(13, 20, 36, 0.75)',
            padding: '22px',
            borderRadius: '12px',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            transition: 'all 0.2s ease',
            display: 'block'
          }}
          className="cyber-hover-card"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <SearchCheck size={20} color="#fbbf24" />
            </div>
            <ArrowRight size={16} color="#64748b" />
          </div>
          <strong style={{ color: '#ffffff', fontSize: '1.05rem', display: 'block', marginBottom: '6px' }}>
            Forensic Investigation
          </strong>
          <span style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, display: 'block' }}>
            Analyze suspected leaked PDFs, extract forensic watermarks, and generate Court of Inquiry dossiers.
          </span>
        </Link>

        {/* Card 4 */}
        <Link
          to="/ledger"
          style={{
            textDecoration: 'none',
            background: 'rgba(13, 20, 36, 0.75)',
            padding: '22px',
            borderRadius: '12px',
            border: '1px solid rgba(168, 85, 247, 0.2)',
            transition: 'all 0.2s ease',
            display: 'block'
          }}
          className="cyber-hover-card"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Network size={20} color="#c084fc" />
            </div>
            <ArrowRight size={16} color="#64748b" />
          </div>
          <strong style={{ color: '#ffffff', fontSize: '1.05rem', display: 'block', marginBottom: '6px' }}>
            Ledger &amp; Consensus Explorer
          </strong>
          <span style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, display: 'block' }}>
            Inspect committed blocks, 2-of-3 quorum validator signatures, and SHA3-256 hash chains.
          </span>
        </Link>
      </div>
    </section>
  );
}
