import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';
import { FileLock, ShieldCheck, Users, Upload, CheckCircle2, AlertTriangle, Layers, Cpu, Radio } from '../../components/Icons.jsx';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Upload & Protect form state
  const [title, setTitle] = useState('Naval Operational Directive 2026-X');
  const [selectedRecipientIds, setSelectedRecipientIds] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [protecting, setProtecting] = useState(false);
  const [selectedDocDetails, setSelectedDocDetails] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [docsRes, recsRes] = await Promise.allSettled([
        apiRequest('/api/v1/documents'),
        apiRequest('/api/v1/recipients'),
      ]);

      if (docsRes.status === 'fulfilled') {
        setDocuments(docsRes.value || []);
      }
      if (recsRes.status === 'fulfilled') {
        const recList = recsRes.value.recipients || [];
        setRecipients(recList);
        if (selectedRecipientIds.length === 0) {
          const activeIds = recList.filter(r => r.status === 'active').map(r => r.recipient_id);
          setSelectedRecipientIds(activeIds.slice(0, 2));
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load document registry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const toggleRecipient = (recId) => {
    setSelectedRecipientIds(prev =>
      prev.includes(recId) ? prev.filter(id => id !== recId) : [...prev, recId]
    );
  };

  const handleProtectDocument = async (e) => {
    e.preventDefault();
    if (selectedRecipientIds.length === 0) {
      setError('Please select at least one recipient to receive an ML-KEM envelope.');
      return;
    }

    try {
      setProtecting(true);
      setError(null);
      setSuccessMsg(null);

      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('recipient_ids', selectedRecipientIds.join(','));
      if (selectedFile) {
        formData.append('file', selectedFile);
      }

      const res = await apiRequest('/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });

      setSuccessMsg(res.message || 'Document encrypted and envelopes generated.');
      setSelectedDocDetails(res.document);
      setSelectedFile(null);
      await fetchData();
    } catch (err) {
      setError(`Document protection failed: ${err.message}`);
    } finally {
      setProtecting(false);
    }
  };

  return (
    <section style={{ maxWidth: '1180px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <FileLock size={24} color="#00f0ff" />
            <h2 style={{ fontSize: '1.85rem', margin: 0, color: '#ffffff', fontWeight: 800, letterSpacing: '0.04em' }}>
              DOCUMENT PROTECTION &amp; PACKAGING
            </h2>
          </div>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.92rem' }}>
            Sender Cryptographic Pipeline &bull; AES-256-GCM Bulk Payload with Multi-Recipient ML-KEM-768 Envelopes
          </p>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          padding: '8px 14px',
          borderRadius: '8px',
          fontSize: '0.78rem',
          color: '#38bdf8',
          fontFamily: 'var(--font-mono)'
        }}>
          <Cpu size={14} color="#38bdf8" />
          <span>ALGORITHM: AES-256-GCM + ML-KEM-768</span>
        </div>
      </header>

      {/* Cryptographic Architecture Invariant Banner */}
      <div style={{
        background: 'rgba(16, 185, 129, 0.08)',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '26px',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
      }}>
        <ShieldCheck size={26} color="#34d399" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.5 }}>
          <strong style={{ color: '#34d399' }}>Hybrid Envelope Invariant:</strong> The document payload is encrypted <em>once</em> with a fresh random 32-byte Content Encryption Key (AES-256-GCM).
          The CEK is encapsulated into <em>N distinct ML-KEM-768 envelopes</em> for authorized officers. Revoking an officer requires zero re-encryption of the bulk payload.
        </div>
      </div>

      {successMsg && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: '10px',
          padding: '12px 18px',
          marginBottom: '22px',
          color: '#34d399',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontFamily: 'var(--font-mono)'
        }}>
          <CheckCircle2 size={16} color="#34d399" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '10px',
          padding: '12px 18px',
          marginBottom: '22px',
          color: '#f87171',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontFamily: 'var(--font-mono)'
        }}>
          <AlertTriangle size={16} color="#ef4444" />
          <span>{error}</span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Upload & Protect Form */}
        <div className="panel" style={{ background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <Upload size={18} color="#00f0ff" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
              Protect &amp; Distribute Directive
            </h3>
          </div>

          <form onSubmit={handleProtectDocument} style={{ display: 'grid', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                DIRECTIVE TITLE / CLASSIFICATION
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                PDF DOCUMENT ATTACHMENT (LEAVE EMPTY FOR SYNTHETIC FIXTURE)
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                style={{ width: '100%', fontSize: '0.82rem', padding: '8px' }}
              />
              <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Default: Generates standard naval operational directive template.'}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                SELECT AUTHORIZED RECIPIENTS (ML-KEM-768 ENVELOPES)
              </label>
              <div style={{
                maxHeight: '160px',
                overflowY: 'auto',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                borderRadius: '8px',
                padding: '10px 12px',
                background: '#090e1a',
                display: 'grid',
                gap: '8px',
              }}>
                {recipients.length === 0 ? (
                  <div style={{ fontSize: '0.82rem', color: '#64748b', padding: '4px' }}>
                    No recipients enrolled. Please enroll recipients on the Recipients tab first.
                  </div>
                ) : (
                  recipients.map(r => (
                    <label
                      key={r.recipient_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        fontSize: '0.82rem',
                        cursor: r.status === 'active' ? 'pointer' : 'not-allowed',
                        opacity: r.status === 'active' ? 1 : 0.45,
                        color: '#f1f5f9'
                      }}
                    >
                      <input
                        type="checkbox"
                        disabled={r.status !== 'active'}
                        checked={selectedRecipientIds.includes(r.recipient_id)}
                        onChange={() => toggleRecipient(r.recipient_id)}
                      />
                      <span>
                        <strong style={{ color: '#ffffff' }}>{r.name}</strong>{' '}
                        <code style={{ color: '#38bdf8' }}>({r.recipient_id})</code>
                        {r.status !== 'active' && <span style={{ color: '#ef4444', marginLeft: '6px', fontWeight: 800 }}>[REVOKED]</span>}
                      </span>
                    </label>
                  ))
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={protecting || recipients.length === 0}
              style={{
                marginTop: '6px',
                padding: '12px 18px',
                backgroundColor: '#00f0ff',
                color: '#060913',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 800,
                fontSize: '0.88rem',
                cursor: protecting ? 'not-allowed' : 'pointer',
                boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)'
              }}
            >
              {protecting ? 'ENCRYPTING & PACKAGING ENVELOPES...' : 'ENCRYPT & GENERATE PQC ENVELOPES'}
            </button>
          </form>
        </div>

        {/* Protection Output Details */}
        <div className="panel" style={{ background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <Layers size={18} color="#34d399" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
              Active Cryptographic Packaging
            </h3>
          </div>

          {selectedDocDetails ? (
            <div style={{ background: 'rgba(6, 11, 22, 0.8)', padding: '18px', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.2)', fontSize: '0.85rem' }}>
              <div style={{ fontWeight: 800, color: '#ffffff', marginBottom: '10px', fontSize: '1rem' }}>
                {selectedDocDetails.title}
              </div>
              <div style={{ display: 'grid', gap: '8px', color: '#cbd5e1', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                <div><span style={{ color: '#64748b' }}>DOC ID:</span> <code style={{ color: '#38bdf8' }}>{selectedDocDetails.document_id}</code></div>
                <div><span style={{ color: '#64748b' }}>SYMMETRIC:</span> <span style={{ color: '#38bdf8', fontWeight: 700 }}>AES-256-GCM (1 shared ciphertext)</span></div>
                <div><span style={{ color: '#64748b' }}>CIPHERTEXT:</span> {selectedDocDetails.ciphertext_size_bytes} bytes</div>
                <div><span style={{ color: '#64748b' }}>ENVELOPES:</span> {selectedDocDetails.envelopes_count} recipient(s)</div>
                <div><span style={{ color: '#64748b' }}>KEM SUITE:</span> <span style={{ color: '#34d399', fontWeight: 700 }}>ML-KEM-768 (NIST FIPS 203)</span></div>
              </div>

              {selectedDocDetails.envelopes && (
                <div style={{ marginTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '12px' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94a3b8', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
                    RECIPIENT ENVELOPE ROSTER:
                  </div>
                  {selectedDocDetails.envelopes.map(env => (
                    <div key={env.recipient_id} style={{ fontSize: '0.76rem', background: '#0b1120', padding: '8px 10px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.15)', marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>👤 <strong style={{ color: '#ffffff' }}>{env.recipient_name}</strong> (<code style={{ color: '#38bdf8' }}>{env.recipient_id}</code>)</span>
                      <span style={{ color: '#34d399', fontFamily: 'var(--font-mono)' }}>KEM CT: 1088B</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: '#64748b', fontSize: '0.88rem', textAlign: 'center', padding: '60px 10px', fontFamily: 'var(--font-mono)' }}>
              SELECT RECIPIENTS AND CLICK ENCRYPT TO VIEW POST-QUANTUM PACKAGING TELEMETRY.
            </div>
          )}
        </div>
      </div>

      {/* Protected Documents Table */}
      <div className="panel" style={{ background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#ffffff', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileLock size={18} color="#00f0ff" />
          Protected Document Registry ({documents.length})
        </h3>

        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: '#64748b', fontSize: '0.9rem', fontFamily: 'var(--font-mono)' }}>
            NO PROTECTED DIRECTIVES REGISTERED IN LOCAL STORAGE.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'left', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                  <th style={{ padding: '12px 10px' }}>DOCUMENT ID</th>
                  <th style={{ padding: '12px 10px' }}>DIRECTIVE TITLE</th>
                  <th style={{ padding: '12px 10px' }}>STATUS</th>
                  <th style={{ padding: '12px 10px' }}>ENVELOPES</th>
                  <th style={{ padding: '12px 10px' }}>CREATED</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.document_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '12px 10px' }}><code style={{ color: '#38bdf8' }}>{doc.document_id}</code></td>
                    <td style={{ padding: '12px 10px', fontWeight: 600, color: '#ffffff' }}>{doc.title}</td>
                    <td style={{ padding: '12px 10px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        color: '#34d399',
                        fontFamily: 'var(--font-mono)'
                      }}>
                        {doc.status.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '12px 10px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        background: 'rgba(56, 189, 248, 0.12)',
                        border: '1px solid rgba(56, 189, 248, 0.3)',
                        color: '#38bdf8',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)'
                      }}>
                        {doc.envelopes_count} OFFICER(S)
                      </span>
                    </td>
                    <td style={{ padding: '12px 10px', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                      {new Date(doc.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
