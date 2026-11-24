import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';
import { Network, ShieldCheck, Cpu, RefreshCw, CheckCircle2, ChevronDown, ChevronUp, Layers, Hash } from '../../components/Icons.jsx';

export default function LedgerPage() {
  const [chain, setChain] = useState([]);
  const [statusInfo, setStatusInfo] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedBlockId, setExpandedBlockId] = useState(null);

  const fetchLedgerData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [chainRes, statusRes, nodesRes] = await Promise.allSettled([
        apiRequest('/api/v1/ledger/chain'),
        apiRequest('/api/v1/ledger/status'),
        apiRequest('/api/v1/nodes/health'),
      ]);

      if (chainRes.status === 'fulfilled') {
        setChain(chainRes.value || []);
      }
      if (statusRes.status === 'fulfilled') {
        setStatusInfo(statusRes.value);
      }
      if (nodesRes.status === 'fulfilled') {
        setNodes(nodesRes.value || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to ledger cluster.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLedgerData();
  }, []);

  return (
    <section style={{ maxWidth: '1180px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Network size={24} color="#00f0ff" />
            <h2 style={{ fontSize: '1.85rem', margin: 0, color: '#ffffff', fontWeight: 800, letterSpacing: '0.04em' }}>
              DISTRIBUTED CONSENSUS LEDGER
            </h2>
          </div>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.92rem' }}>
            Byzantine Fault Tolerant 2-of-3 Quorum Consensus &bull; SHA3-256 Hash Chain &bull; ML-DSA-65 Validator Signatures
          </p>
        </div>

        <button
          onClick={fetchLedgerData}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(0, 240, 255, 0.1)',
            border: '1px solid rgba(0, 240, 255, 0.35)',
            color: '#00f0ff',
            padding: '8px 16px',
            borderRadius: '8px',
            fontSize: '0.82rem',
            fontWeight: 700,
            cursor: 'pointer',
            fontFamily: 'var(--font-mono)'
          }}
        >
          <RefreshCw size={14} className={loading ? 'pulse-beacon' : ''} />
          <span>SYNC LEDGER</span>
        </button>
      </header>

      {/* Consensus Integrity Banner */}
      <div style={{
        background: 'rgba(16, 185, 129, 0.08)',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        borderRadius: '10px',
        padding: '18px 22px',
        marginBottom: '26px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <ShieldCheck size={26} color="#34d399" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 800, color: '#ffffff', fontSize: '0.98rem' }}>
              Consensus Protocol: 2-of-3 Byzantine Quorum &bull; SHA3-256 Hash Chain
            </div>
            <div style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '3px' }}>
              Every committed block strictly requires matching ML-DSA-65 signatures from at least 2 distinct physical validator nodes.
            </div>
          </div>
        </div>

        {statusInfo && (
          <div style={{ display: 'flex', gap: '20px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>
            <div>
              <span style={{ color: '#64748b' }}>HEIGHT:</span>{' '}
              <strong style={{ color: '#00f0ff' }}>{statusInfo.chain_height} BLOCKS</strong>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>CONTINUITY:</span>{' '}
              <strong style={{ color: statusInfo.chain_continuity_verified ? '#34d399' : '#ef4444' }}>
                {statusInfo.chain_continuity_verified ? 'CRYPTOGRAPHICALLY SEALED' : 'CHAIN COMPROMISED'}
              </strong>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '10px',
          padding: '14px 18px',
          marginBottom: '22px',
          color: '#f87171',
          fontSize: '0.9rem',
          fontFamily: 'var(--font-mono)'
        }}>
          ALERT: {error}
        </div>
      )}

      {/* 3 Validator Cluster Node Cards */}
      <h3 style={{ fontSize: '1.05rem', color: '#e2e8f0', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px', letterSpacing: '0.04em' }}>
        <Cpu size={16} color="#00f0ff" />
        INDEPENDENT VALIDATOR CLUSTER (3-NODE BYZANTINE FAULT TOLERANCE)
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        {nodes.map(n => (
          <div key={n.node_id} style={{
            background: 'rgba(13, 20, 36, 0.85)',
            borderRadius: '10px',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            padding: '18px 20px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <strong style={{ fontSize: '0.98rem', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{n.node_id.toUpperCase()}</strong>
              <span style={{
                fontSize: '0.7rem',
                padding: '3px 8px',
                borderRadius: '4px',
                fontWeight: 800,
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                color: '#34d399',
                fontFamily: 'var(--font-mono)'
              }}>
                {n.status.toUpperCase()}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'grid', gap: '6px', fontFamily: 'var(--font-mono)' }}>
              <div><span style={{ color: '#64748b' }}>SOCKET:</span> <code style={{ color: '#38bdf8' }}>{n.url}</code></div>
              <div><span style={{ color: '#64748b' }}>DSA SUITE:</span> <span style={{ color: '#34d399', fontWeight: 700 }}>{n.pqc_algorithm}</span></div>
              <div><span style={{ color: '#64748b' }}>ROLE:</span> {n.role.toUpperCase()}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Committed Blocks Timeline */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '1.05rem', color: '#e2e8f0', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', letterSpacing: '0.04em' }}>
          <Layers size={16} color="#00f0ff" />
          IMMUTABLE BLOCK CHAIN TIMELINE ({chain.length} BLOCKS)
        </h3>
      </div>

      <div style={{ display: 'grid', gap: '16px', marginBottom: '32px' }}>
        {chain.length === 0 ? (
          <div style={{ background: 'rgba(13, 20, 36, 0.85)', padding: '40px', textAlign: 'center', borderRadius: '12px', border: '1px solid rgba(56, 189, 248, 0.2)', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
            NO COMMITTED BLOCKS RECORDED IN CLUSTER STORAGE.
          </div>
        ) : (
          chain.map((blk) => {
            const isExpanded = expandedBlockId === blk.block_id;
            return (
              <div
                key={blk.block_id}
                style={{
                  background: 'rgba(13, 20, 36, 0.85)',
                  borderRadius: '12px',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  padding: '20px 24px',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{
                      background: 'rgba(0, 240, 255, 0.15)',
                      border: '1px solid rgba(0, 240, 255, 0.4)',
                      color: '#00f0ff',
                      fontWeight: 800,
                      fontSize: '0.78rem',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)'
                    }}>
                      BLOCK #{blk.sequence}
                    </span>
                    <strong style={{ fontSize: '1rem', color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{blk.block_id}</strong>
                  </div>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid rgba(16, 185, 129, 0.35)',
                    color: '#34d399',
                    fontFamily: 'var(--font-mono)'
                  }}>
                    {blk.status.toUpperCase()}
                  </span>
                </div>

                <div style={{ display: 'grid', gap: '8px', fontSize: '0.8rem', color: '#cbd5e1', fontFamily: 'var(--font-mono)' }}>
                  <div>
                    <span style={{ color: '#64748b' }}>BLOCK HASH (SHA3-256):</span>{' '}
                    <code style={{ color: '#00f0ff' }}>{blk.block_hash}</code>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>PREVIOUS HASH:</span>{' '}
                    <code style={{ color: '#94a3b8' }}>{blk.previous_hash}</code>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>MERKLE ROOT:</span>{' '}
                    <code style={{ color: '#cbd5e1' }}>{blk.merkle_root}</code>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>COMMITTED PROPOSALS:</span>{' '}
                    <span style={{ color: '#34d399', fontWeight: 700 }}>{blk.proposals_count} VERIFIED EVENT(S)</span>
                  </div>
                </div>

                {blk.proposals && blk.proposals.length > 0 && (
                  <div style={{ marginTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '12px' }}>
                    <button
                      onClick={() => setExpandedBlockId(isExpanded ? null : blk.block_id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#38bdf8',
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        padding: 0,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      {isExpanded ? 'COLLAPSE PROPOSAL DETAILS' : `INSPECT ${blk.proposals.length} CANONICAL PROPOSAL EVENT(S)`}
                    </button>

                    {isExpanded && (
                      <div style={{ marginTop: '12px', display: 'grid', gap: '10px' }}>
                        {blk.proposals.map((prop, pIdx) => (
                          <pre
                            key={pIdx}
                            style={{
                              background: '#060913',
                              border: '1px solid rgba(56, 189, 248, 0.2)',
                              color: '#67e8f9',
                              padding: '14px',
                              borderRadius: '8px',
                              fontSize: '0.74rem',
                              overflowX: 'auto',
                              fontFamily: 'var(--font-mono)'
                            }}
                          >
                            {JSON.stringify(prop, null, 2)}
                          </pre>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
