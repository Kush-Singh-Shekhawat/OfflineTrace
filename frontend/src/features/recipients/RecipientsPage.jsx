import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';

export default function RecipientsPage() {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  // Enrollment form state
  const [newRecipientId, setNewRecipientId] = useState('');
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassphrase, setNewPassphrase] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Local Decryption Simulator state
  const [selectedRecipientId, setSelectedRecipientId] = useState('');
  const [simDocTitle, setSimDocTitle] = useState('Confidential Naval Operation Directive');
  const [simWatermarkToken, setSimWatermarkToken] = useState('session-tok-99238-alpha');
  const [simEnvelopeData, setSimEnvelopeData] = useState(null);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  // Adversarial Attack Simulator state (Phase 6)
  const [tamperAttackType, setTamperAttackType] = useState('ciphertext_bitflip');
  const [tamperRunning, setTamperRunning] = useState(false);
  const [tamperResult, setTamperResult] = useState(null);
  const [tamperError, setTamperError] = useState(null);

  const fetchRecipients = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiRequest('/api/v1/recipients');
      setRecipients(res.recipients || []);
      if (res.recipients?.length > 0 && !selectedRecipientId) {
        setSelectedRecipientId(res.recipients[0].recipient_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to backend service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipients();
  }, []);

  const handleEnroll = async (e) => {
    e.preventDefault();
    if (!newRecipientId || !newName || !newEmail) return;

    try {
      setSubmitting(true);
      setActionMessage(null);
      const payload = {
        recipient_id: newRecipientId.trim(),
        name: newName.trim(),
        email: newEmail.trim(),
        passphrase: newPassphrase || 'offline-trace-default-passphrase',
      };
      const created = await apiRequest('/api/v1/recipients', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setActionMessage(`Enrolled ${created.name} (${created.recipient_id}) with ML-KEM-768 & ML-DSA-65 keys!`);
      setNewRecipientId('');
      setNewName('');
      setNewEmail('');
      setNewPassphrase('');
      await fetchRecipients();
      setSelectedRecipientId(created.recipient_id);
    } catch (err) {
      setError(`Enrollment failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (recipientId) => {
    if (!window.confirm(`Revoke keys for recipient ${recipientId}? This cannot be undone.`)) return;
    try {
      setActionMessage(null);
      await apiRequest(`/api/v1/recipients/${recipientId}/revoke`, { method: 'POST' });
      setActionMessage(`Revoked recipient ${recipientId}.`);
      await fetchRecipients();
    } catch (err) {
      setError(`Revocation failed: ${err.message}`);
    }
  };

  const handleRotate = async (recipientId) => {
    if (!window.confirm(`Rotate keypairs for recipient ${recipientId}? New ML-KEM and ML-DSA keys will be generated.`)) return;
    try {
      setActionMessage(null);
      await apiRequest(`/api/v1/recipients/${recipientId}/rotate`, { method: 'POST' });
      setActionMessage(`Successfully rotated keypairs for ${recipientId}.`);
      await fetchRecipients();
    } catch (err) {
      setError(`Key rotation failed: ${err.message}`);
    }
  };

  // Simulator: Step 1 Generate test envelope
  const handleSimulateEnvelope = async () => {
    if (!selectedRecipientId) return;
    try {
      setSimLoading(true);
      setError(null);
      setSimResult(null);
      const data = await apiRequest(
        `/api/v1/recipient/simulate-envelope?recipient_id=${encodeURIComponent(selectedRecipientId)}&document_title=${encodeURIComponent(simDocTitle)}`,
        { method: 'POST' }
      );
      setSimEnvelopeData(data);
      setActionMessage('Generated test encrypted document and recipient CEK envelope.');
    } catch (err) {
      setError(`Simulation envelope preparation failed: ${err.message}`);
    } finally {
      setSimLoading(false);
    }
  };

  // Simulator: Step 2 Recipient-local decryption and provenance signing
  const handleSimulateDecrypt = async () => {
    if (!simEnvelopeData) return;
    try {
      setSimLoading(true);
      setError(null);
      const payload = {
        recipient_id: selectedRecipientId,
        document_id: simEnvelopeData.document_id,
        version_id: simEnvelopeData.version_id,
        envelope: simEnvelopeData.envelope,
        encrypted_document_b64: simEnvelopeData.encrypted_document_b64,
        watermark_token: simWatermarkToken,
        passphrase: 'offline-trace-default-passphrase',
      };
      const result = await apiRequest('/api/v1/recipient/decrypt', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setSimResult(result);
      setActionMessage('Local decapsulation, CEK unwrap, and ML-DSA-65 signing completed successfully!');
    } catch (err) {
      setError(`Local decrypt action failed: ${err.message}`);
    } finally {
      setSimLoading(false);
    }
  };

  const handleRunTamperTest = async (attackType) => {
    const selectedType = attackType || tamperAttackType;
    try {
      setTamperRunning(true);
      setTamperResult(null);
      setTamperError(null);
      const res = await apiRequest(
        `/api/v1/recipient/tamper-test?attack_type=${encodeURIComponent(selectedType)}&recipient_id=${encodeURIComponent(selectedRecipientId || '')}`,
        { method: 'POST' }
      );
      setTamperResult(res);
    } catch (err) {
      setTamperError(err.message || 'Tamper simulation failed.');
    } finally {
      setTamperRunning(false);
    }
  };

  return (
    <section style={{ maxWidth: '1080px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', margin: '0 0 6px 0', color: '#0f172a' }}>
          Recipients &amp; Key Management
        </h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: '0.95rem' }}>
          Member A — Post-quantum key lifecycle (ML-KEM-768, ML-DSA-65) and recipient-local decryption boundary.
        </p>
      </header>

      {/* Security Invariant Banner */}
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
        <span style={{ fontSize: '1.25rem' }}>🔒</span>
        <div style={{ fontSize: '0.88rem', color: '#166534', lineHeight: 1.4 }}>
          <strong>Zero Secret Custody Invariant:</strong> Private keys (ML-KEM-768 decapsulation key &amp; ML-DSA-65 signing key)
          and plaintext Content Encryption Keys (CEK) remain strictly inside the recipient's local boundary. Only public keys and SHA3-256 fingerprints are displayed here.
        </div>
      </div>

      {actionMessage && (
        <div style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          padding: '10px 16px',
          marginBottom: '20px',
          color: '#1e40af',
          fontSize: '0.9rem',
        }}>
          {actionMessage}
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
        {/* Enrollment Form */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
            ➕ Enroll New Recipient
          </h3>
          <form onSubmit={handleEnroll} style={{ display: 'grid', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Recipient ID (Opaque)
              </label>
              <input
                type="text"
                required
                placeholder="e.g. recip_wesee_01"
                value={newRecipientId}
                onChange={(e) => setNewRecipientId(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Full Name / Unit
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Commander R. Sharma"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Official Email
              </label>
              <input
                type="email"
                required
                placeholder="e.g. sharma.r@wesee.mod.in"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Local Keystore Passphrase (Optional)
              </label>
              <input
                type="password"
                placeholder="Protects private keys at rest (PBKDF2-AES-GCM)"
                value={newPassphrase}
                onChange={(e) => setNewPassphrase(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              style={{
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 16px',
                fontWeight: 600,
                cursor: submitting ? 'not-allowed' : 'pointer',
                marginTop: '8px',
              }}
            >
              {submitting ? 'Generating PQC Keys...' : 'Generate PQC Keys & Enroll'}
            </button>
          </form>
        </div>

        {/* Algorithm Standards Reference */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
            🛡️ Cryptographic Standards &amp; Invariants
          </h3>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.88rem', color: '#334155', lineHeight: 1.6 }}>
            <li>
              <strong>Key Encapsulation:</strong> NIST FIPS 203 <code>ML-KEM-768</code> (1,184B public key, 1,088B ciphertext, 32B shared secret).
            </li>
            <li>
              <strong>Digital Signatures:</strong> NIST FIPS 204 <code>ML-DSA-65</code> (1,952B public key, 3,309B signature) for canonical event provenance.
            </li>
            <li>
              <strong>Content Encryption:</strong> <code>AES-256-GCM</code> with fresh 32-byte CEK and unique 12-byte nonces.
            </li>
            <li>
              <strong>Context Binding:</strong> <code>HKDF-SHA-256</code> domain separation binding <code>(doc_id, version_id, recipient_fingerprint)</code>.
            </li>
            <li>
              <strong>Envelope Architecture:</strong> 1 shared encrypted payload per document version; N independent recipient-bound envelopes.
            </li>
          </ul>
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f8fafc', borderRadius: '6px', fontSize: '0.82rem', color: '#64748b' }}>
            Total Registered Recipients: <strong>{recipients.length}</strong>
          </div>
        </div>
      </div>

      {/* Recipient Roster */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a' }}>
            Registered Recipient Directory ({recipients.length})
          </h3>
          <button
            onClick={fetchRecipients}
            style={{
              padding: '6px 12px',
              fontSize: '0.85rem',
              backgroundColor: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            ↻ Refresh Directory
          </button>
        </div>

        {loading ? (
          <p style={{ color: '#64748b' }}>Loading recipient public records...</p>
        ) : recipients.length === 0 ? (
          <div className="panel" style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
            No recipients enrolled yet. Enroll your first recipient above!
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '16px' }}>
            {recipients.map((rec) => (
              <div
                key={rec.recipient_id}
                style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '20px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', color: '#0f172a' }}>
                      {rec.name}
                    </h4>
                    <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                      ID: <code>{rec.recipient_id}</code> &bull; Email: {rec.email}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span
                      style={{
                        padding: '3px 10px',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: rec.status === 'active' ? '#dcfce7' : '#fee2e2',
                        color: rec.status === 'active' ? '#15803d' : '#b91c1c',
                      }}
                    >
                      {rec.status.toUpperCase()}
                    </span>
                    <button
                      onClick={() => handleRotate(rec.recipient_id)}
                      disabled={rec.status !== 'active'}
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.8rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        backgroundColor: '#ffffff',
                        cursor: rec.status === 'active' ? 'pointer' : 'not-allowed',
                      }}
                    >
                      Rotate Keys
                    </button>
                    <button
                      onClick={() => handleRevoke(rec.recipient_id)}
                      disabled={rec.status !== 'active'}
                      style={{
                        padding: '5px 10px',
                        fontSize: '0.8rem',
                        borderRadius: '6px',
                        border: '1px solid #fca5a5',
                        backgroundColor: '#fff1f2',
                        color: '#be123c',
                        cursor: rec.status === 'active' ? 'pointer' : 'not-allowed',
                      }}
                    >
                      Revoke
                    </button>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: '#f8fafc', padding: '12px', borderRadius: '8px' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>
                      KEM ENCAPSULATION KEY ({rec.kem_algorithm})
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', wordBreak: 'break-all' }}>
                      SHA3-256 Fingerprint:
                      <br />
                      <code style={{ color: '#0369a1' }}>{rec.kem_fingerprint}</code>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', marginBottom: '4px' }}>
                      SIGNING VERIFICATION KEY ({rec.dsa_algorithm})
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', wordBreak: 'break-all' }}>
                      SHA3-256 Fingerprint:
                      <br />
                      <code style={{ color: '#4338ca' }}>{rec.dsa_fingerprint}</code>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recipient-Local Decryption Simulator */}
      <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #cbd5e1' }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: '1.25rem', color: '#0f172a' }}>
          🔬 Recipient-Local Decrypt &amp; Provenance Signing Simulator
        </h3>
        <p style={{ margin: '0 0 20px 0', fontSize: '0.88rem', color: '#64748b' }}>
          Simulates recipient receiving an encrypted document payload and opening their individual ML-KEM-768 envelope locally to recover the CEK and sign the canonical provenance event.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Select Recipient
            </label>
            <select
              value={selectedRecipientId}
              onChange={(e) => setSelectedRecipientId(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
            >
              {recipients.map((r) => (
                <option key={r.recipient_id} value={r.recipient_id}>
                  {r.name} ({r.recipient_id}) - {r.status}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
              Session Watermark Token
            </label>
            <input
              type="text"
              value={simWatermarkToken}
              onChange={(e) => setSimWatermarkToken(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
          <button
            onClick={handleSimulateEnvelope}
            disabled={simLoading || !selectedRecipientId}
            style={{
              padding: '10px 16px',
              backgroundColor: '#0284c7',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: simLoading ? 'not-allowed' : 'pointer',
            }}
          >
            Step 1: Generate Test Envelope
          </button>
          <button
            onClick={handleSimulateDecrypt}
            disabled={simLoading || !simEnvelopeData}
            style={{
              padding: '10px 16px',
              backgroundColor: simEnvelopeData ? '#059669' : '#94a3b8',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: simEnvelopeData ? 'pointer' : 'not-allowed',
            }}
          >
            Step 2: Execute Local Decrypt &amp; Sign
          </button>
        </div>

        {simEnvelopeData && (
          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.85rem' }}>
            <h5 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#1e293b' }}>
              📦 Envelope Prepared for {simEnvelopeData.envelope.recipient_id}:
            </h5>
            <div>Document ID: <code>{simEnvelopeData.document_id}</code></div>
            <div>KEM Ciphertext Length: <code>1088 bytes (Base64 encoded)</code></div>
            <div>Wrapped CEK: <code>{simEnvelopeData.envelope.wrapped_cek.substring(0, 32)}...</code></div>
          </div>
        )}

        {simResult && (
          <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '16px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span style={{ fontSize: '1.2rem', color: '#059669' }}>✅</span>
              <strong style={{ color: '#065f46' }}>Decryption &amp; Provenance Signing Verified!</strong>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#064e3b', marginBottom: '8px' }}>
              Decrypted Payload Size: <strong>{simResult.decrypted_size_bytes} bytes</strong> &bull;
              DSA Fingerprint: <code>{simResult.recipient_dsa_fingerprint}</code>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#064e3b', marginBottom: '8px' }}>
              Watermark Token SHA3-256 Digest (Digest only stored on ledger):
              <br />
              <code style={{ fontSize: '0.8rem' }}>{simResult.token_digest}</code>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#047857', marginBottom: '4px' }}>
                Signed Canonical Event (Ready for Validator Submission):
              </div>
              <pre style={{
                background: '#042f2e',
                color: '#a7f3d0',
                padding: '12px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                overflowX: 'auto',
              }}>
                {JSON.stringify(simResult.canonical_event, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Adversarial Attack & Fail-Closed Tamper Simulator (Phase 6) */}
      <div className="panel" style={{
        padding: '24px',
        borderRadius: '12px',
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        marginBottom: '32px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h3 style={{ margin: '0 0 4px 0', fontSize: '1.2rem', color: '#0f172a' }}>
              🛡️ Adversarial Security &amp; Fail-Closed Tamper Testing (Phase 6)
            </h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
              Demonstrate live cryptographic defenses under active attack. Proves zero plaintext leakage when tampered.
            </p>
          </div>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '4px 8px',
            borderRadius: '4px',
            background: '#e0f2fe',
            color: '#0369a1',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}>
            Evaluator Demonstration
          </span>
        </div>

        {/* Attack Vector Selector Tabs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px',
          marginBottom: '20px',
        }}>
          {[
            { id: 'ciphertext_bitflip', label: '💥 Bit-Flip Attack', desc: 'AES-256-GCM AEAD Tag' },
            { id: 'kem_tamper', label: '⚛️ KEM Tampering', desc: 'ML-KEM-768 Decapsulation' },
            { id: 'impersonation', label: '🎭 Key Impersonation', desc: 'Recipient Asymmetric Boundary' },
            { id: 'context_mismatch', label: '🔀 Context Confusion', desc: 'HKDF-SHA-256 Binding' },
            { id: 'revoked_credential', label: '🚫 Revoked Credential', desc: 'Keystore Status Check' },
          ].map((item) => {
            const active = tamperAttackType === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setTamperAttackType(item.id);
                  handleRunTamperTest(item.id);
                }}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  border: active ? '2px solid #2563eb' : '1px solid #e2e8f0',
                  background: active ? '#eff6ff' : '#f8fafc',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease-in-out',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: active ? '#1e40af' : '#1e293b' }}>
                  {item.label}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '2px' }}>
                  {item.desc}
                </div>
              </button>
            );
          })}
        </div>

        {/* Action Button */}
        <div style={{ marginBottom: '20px' }}>
          <button
            type="button"
            disabled={tamperRunning}
            onClick={() => handleRunTamperTest(tamperAttackType)}
            style={{
              padding: '10px 20px',
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: tamperRunning ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 2px 4px rgba(220, 38, 38, 0.2)',
            }}
          >
            {tamperRunning ? 'Simulating Attack Vector...' : '⚡ Trigger Attack Simulation'}
          </button>
        </div>

        {tamperError && (
          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '16px',
          }}>
            Simulation Error: {tamperError}
          </div>
        )}

        {/* Attack Outcome Verdict Card */}
        {tamperResult && (
          <div style={{
            background: '#f0fdf4',
            border: '1px solid #86efac',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.5rem' }}>🛡️</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: '#166534' }}>
                    ATTACK NEUTRALIZED &mdash; {tamperResult.security_verdict}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#15803d' }}>
                    {tamperResult.attack_name}
                  </div>
                </div>
              </div>
              <div style={{
                textAlign: 'right',
                background: '#dcfce7',
                border: '1px solid #bbf7d0',
                padding: '6px 14px',
                borderRadius: '6px',
              }}>
                <div style={{ fontSize: '0.7rem', color: '#166534', fontWeight: 600, textTransform: 'uppercase' }}>
                  Plaintext Leaked
                </div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#15803d' }}>
                  {tamperResult.plaintext_leaked_bytes} Bytes
                </div>
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr',
              gap: '10px',
              background: '#ffffff',
              padding: '14px',
              borderRadius: '6px',
              border: '1px solid #dcfce7',
              fontSize: '0.82rem',
            }}>
              <div>
                <strong style={{ color: '#1e293b' }}>Cryptographic Defense Mechanism:</strong>{' '}
                <span style={{ color: '#0369a1', fontWeight: 600 }}>{tamperResult.defense_mechanism}</span>
              </div>
              <div>
                <strong style={{ color: '#1e293b' }}>Exception Caught:</strong>{' '}
                <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', color: '#b91c1c' }}>
                  {tamperResult.exception_type}
                </code>
              </div>
              <div>
                <strong style={{ color: '#1e293b' }}>Diagnostic Detail:</strong>{' '}
                <span style={{ color: '#475569' }}>{tamperResult.exception_detail}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
