import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';

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
      formData.append('title', title.trim() || 'Classified Naval Directive');
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
    <section style={{ maxWidth: '1080px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', margin: '0 0 6px 0', color: '#0f172a' }}>
          Document Protection &amp; Distribution
        </h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: '0.95rem' }}>
          Sender Workflow — Bulk AES-256-GCM encryption with per-recipient ML-KEM-768 post-quantum key envelopes.
        </p>
      </header>

      {/* Cryptographic Architecture Invariant Banner */}
      <div style={{
        backgroundColor: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: '8px',
        padding: '12px 16px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <span style={{ fontSize: '1.25rem' }}>🔐</span>
        <div style={{ fontSize: '0.88rem', color: '#166534', lineHeight: 1.4 }}>
          <strong>Hybrid Envelope Invariant:</strong> The document payload is encrypted <em>once</em> with a fresh random 32-byte Content Encryption Key (AES-256-GCM).
          The CEK is encapsulated into <em>N distinct ML-KEM-768 envelopes</em> for authorized officers. Revoking an officer requires zero re-encryption of the document.
        </div>
      </div>

      {successMsg && (
        <div style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          padding: '10px 16px',
          marginBottom: '20px',
          color: '#1e40af',
          fontSize: '0.9rem',
        }}>
          {successMsg}
        </div>
      )}

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '10px 16px',
          marginBottom: '20px',
          color: '#991b1b',
          fontSize: '0.9rem',
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Upload & Protect Form */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
            🔒 Protect &amp; Distribute Document
          </h3>

          <form onSubmit={handleProtectDocument} style={{ display: 'grid', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Document Title / Directive
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Upload PDF Document (Optional — Generates Synthetic if Empty)
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
              />
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Default: Generates standard naval operational directive template.'}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                Select Authorized Recipients (ML-KEM-768 Envelopes)
              </label>
              <div style={{
                maxHeight: '160px',
                overflowY: 'auto',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                padding: '8px',
                background: '#f8fafc',
                display: 'grid',
                gap: '6px',
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
                        gap: '8px',
                        fontSize: '0.82rem',
                        cursor: r.status === 'active' ? 'pointer' : 'not-allowed',
                        opacity: r.status === 'active' ? 1 : 0.5,
                      }}
                    >
                      <input
                        type="checkbox"
                        disabled={r.status !== 'active'}
                        checked={selectedRecipientIds.includes(r.recipient_id)}
                        onChange={() => toggleRecipient(r.recipient_id)}
                      />
                      <span>
                        <strong>{r.name}</strong> ({r.recipient_id})
                        {r.status !== 'active' && <span style={{ color: '#dc2626', marginLeft: '6px' }}>[REVOKED]</span>}
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
                marginTop: '8px',
                padding: '10px 16px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                cursor: protecting ? 'not-allowed' : 'pointer',
              }}
            >
              {protecting ? 'Encrypting & Packaging Envelopes...' : '🚀 Encrypt & Generate PQC Envelopes'}
            </button>
          </form>
        </div>

        {/* Protection Output Details */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
            📦 Active Cryptographic Packaging
          </h3>

          {selectedDocDetails ? (
            <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.85rem' }}>
              <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '8px', fontSize: '0.95rem' }}>
                {selectedDocDetails.title}
              </div>
              <div style={{ display: 'grid', gap: '6px', color: '#334155' }}>
                <div><strong>Document ID:</strong> <code>{selectedDocDetails.document_id}</code></div>
                <div><strong>Symmetric Cipher:</strong> <span style={{ color: '#0284c7', fontWeight: 600 }}>AES-256-GCM (1 shared ciphertext)</span></div>
                <div><strong>Ciphertext Size:</strong> {selectedDocDetails.ciphertext_size_bytes} bytes</div>
                <div><strong>Generated Envelopes:</strong> {selectedDocDetails.envelopes_count} recipient(s)</div>
                <div><strong>KEM Algorithm:</strong> <span style={{ color: '#15803d', fontWeight: 600 }}>ML-KEM-768 (NIST FIPS 203)</span></div>
              </div>

              {selectedDocDetails.envelopes && (
                <div style={{ marginTop: '12px', borderTop: '1px solid #cbd5e1', paddingTop: '10px' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                    Recipient Envelope Breakdown:
                  </div>
                  {selectedDocDetails.envelopes.map(env => (
                    <div key={env.recipient_id} style={{ fontSize: '0.75rem', background: '#ffffff', padding: '6px 8px', borderRadius: '4px', border: '1px solid #e2e8f0', marginBottom: '4px' }}>
                      👤 <strong>{env.recipient_name}</strong> (<code>{env.recipient_id}</code>) &bull; KEM CT: 1088B
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: '#64748b', fontSize: '0.88rem', textAlign: 'center', padding: '40px 10px' }}>
              Select recipients and click <strong>Encrypt &amp; Generate PQC Envelopes</strong> to see the cryptographic packaging breakdown here.
            </div>
          )}
        </div>
      </div>

      {/* Protected Documents Table */}
      <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
          📑 Protected Document Registry ({documents.length})
        </h3>

        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: '#64748b', fontSize: '0.9rem' }}>
            No protected documents registered yet. Upload and protect your first directive above!
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569' }}>
                  <th style={{ padding: '10px' }}>Document ID</th>
                  <th style={{ padding: '10px' }}>Directive Title</th>
                  <th style={{ padding: '10px' }}>Status</th>
                  <th style={{ padding: '10px' }}>Envelopes</th>
                  <th style={{ padding: '10px' }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.document_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '10px' }}><code>{doc.document_id}</code></td>
                    <td style={{ padding: '10px', fontWeight: 600, color: '#1e293b' }}>{doc.title}</td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: '#dcfce7',
                        color: '#15803d',
                      }}>
                        {doc.status}
                      </span>
                    </td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        background: '#e0f2fe',
                        color: '#0369a1',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                      }}>
                        {doc.envelopes_count} Officer(s)
                      </span>
                    </td>
                    <td style={{ padding: '10px', color: '#64748b' }}>
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
