import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';

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
    <section style={{ maxWidth: '1080px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', margin: '0 0 6px 0', color: '#0f172a' }}>
          Immutable Distributed Ledger Explorer
        </h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: '0.95rem' }}>
          Member C Component — 2-of-3 Byzantine Fault Tolerant consensus blocks, SHA3-256 hash chains, and validator signatures.
        </p>
      </header>

      {/* Consensus Integrity Banner */}
      <div style={{
        backgroundColor: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.5rem' }}>⛓️</span>
          <div>
            <div style={{ fontWeight: 700, color: '#166534', fontSize: '0.95rem' }}>
              Consensus Model: 2-of-3 Byzantine Quorum &bull; SHA3-256 Hash Chain
            </div>
            <div style={{ fontSize: '0.82rem', color: '#15803d', marginTop: '2px' }}>
              Every committed block requires matching signatures from at least 2 distinct independent validator nodes.
            </div>
          </div>
        </div>

        {statusInfo && (
          <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: '#475569' }}>Chain Height:</span>{' '}
              <strong style={{ color: '#0f172a' }}>{statusInfo.chain_height} Blocks</strong>
            </div>
            <div>
              <span style={{ color: '#475569' }}>Continuity:</span>{' '}
              <strong style={{ color: statusInfo.chain_continuity_verified ? '#15803d' : '#b91c1c' }}>
                {statusInfo.chain_continuity_verified ? '✅ Verified Intact' : '❌ Broken'}
              </strong>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '20px',
          color: '#991b1b',
          fontSize: '0.9rem',
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* 3 Validator Cluster Node Cards */}
      <h3 style={{ fontSize: '1.15rem', color: '#1e293b', marginBottom: '12px' }}>
        🏛️ Independent Validator Nodes (3-Node Cluster)
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
        {nodes.map(n => (
          <div key={n.node_id} style={{
            background: '#ffffff',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>{n.node_id.toUpperCase()}</strong>
              <span style={{
                fontSize: '0.72rem',
                padding: '2px 8px',
                borderRadius: '4px',
                fontWeight: 700,
                background: '#dcfce7',
                color: '#15803d',
              }}>
                {n.status}
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', display: 'grid', gap: '4px' }}>
              <div>URL: <code>{n.url}</code></div>
              <div>Algorithm: <span style={{ color: '#0284c7', fontWeight: 600 }}>{n.pqc_algorithm}</span></div>
              <div>Role: {n.role}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Committed Blocks Timeline */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '1.15rem', color: '#1e293b', margin: 0 }}>
          📦 Committed Ledger Blocks ({chain.length})
        </h3>
        <button
          onClick={fetchLedgerData}
          style={{
            padding: '6px 12px',
            background: '#f1f5f9',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          🔄 Refresh Chain
        </button>
      </div>

      <div style={{ display: 'grid', gap: '16px', marginBottom: '32px' }}>
        {chain.length === 0 ? (
          <div style={{ background: '#ffffff', padding: '32px', textAlign: 'center', borderRadius: '12px', border: '1px solid #e2e8f0', color: '#64748b' }}>
            No committed blocks currently recorded.
          </div>
        ) : (
          chain.map((blk, idx) => {
            const isExpanded = expandedBlockId === blk.block_id;
            return (
              <div
                key={blk.block_id}
                style={{
                  background: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '20px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  transition: 'all 0.15s ease-in-out',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      background: '#0f172a',
                      color: '#ffffff',
                      fontWeight: 800,
                      fontSize: '0.8rem',
                      padding: '4px 8px',
                      borderRadius: '4px',
                    }}>
                      #{blk.sequence}
                    </span>
                    <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{blk.block_id}</strong>
                  </div>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    background: '#dcfce7',
                    color: '#15803d',
                  }}>
                    {blk.status}
                  </span>
                </div>

                <div style={{ display: 'grid', gap: '6px', fontSize: '0.82rem', color: '#334155' }}>
                  <div>
                    <strong style={{ color: '#475569' }}>Block Hash (SHA3-256):</strong>{' '}
                    <code style={{ fontSize: '0.78rem', color: '#0284c7' }}>{blk.block_hash}</code>
                  </div>
                  <div>
                    <strong style={{ color: '#475569' }}>Previous Hash:</strong>{' '}
                    <code style={{ fontSize: '0.78rem', color: '#64748b' }}>{blk.previous_hash}</code>
                  </div>
                  <div>
                    <strong style={{ color: '#475569' }}>Merkle Root:</strong>{' '}
                    <code style={{ fontSize: '0.78rem' }}>{blk.merkle_root}</code>
                  </div>
                  <div>
                    <strong style={{ color: '#475569' }}>Committed Proposals:</strong>{' '}
                    <span>{blk.proposals_count} Verified Event(s)</span>
                  </div>
                </div>

                {blk.proposals && blk.proposals.length > 0 && (
                  <div style={{ marginTop: '12px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
                    <button
                      onClick={() => setExpandedBlockId(isExpanded ? null : blk.block_id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#2563eb',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        padding: 0,
                      }}
                    >
                      {isExpanded ? '▲ Hide Proposals' : `▼ Inspect ${blk.proposals.length} Committed Proposals`}
                    </button>

                    {isExpanded && (
                      <div style={{ marginTop: '10px', display: 'grid', gap: '8px' }}>
                        {blk.proposals.map((prop, pIdx) => (
                          <pre
                            key={pIdx}
                            style={{
                              background: '#0f172a',
                              color: '#a5f3fc',
                              padding: '12px',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              overflowX: 'auto',
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
