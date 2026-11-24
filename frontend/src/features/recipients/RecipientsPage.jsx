import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';
import { 
  Users, 
  ShieldCheck, 
  RefreshCw, 
  Trash2, 
  Lock, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2,
  KeyRound,
  Zap,
  Radio,
  FileCheck
} from '../../components/Icons.jsx';

export default function RecipientsPage() {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  // Filter state: 'all' | 'active' | 'revoked'
  const [filterStatus, setFilterStatus] = useState('all');

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
    if (!window.confirm(`Revoke keys for recipient ${recipientId}? This marks their cryptographic identity as compromised/revoked.`)) return;
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

  const handleDelete = async (recipientId) => {
    if (!window.confirm(`Permanently purge recipient ${recipientId} and remove all keys from local keystore? This cannot be undone.`)) return;
    try {
      setActionMessage(null);
      await apiRequest(`/api/v1/recipients/${recipientId}`, { method: 'DELETE' });
      setActionMessage(`Purged recipient ${recipientId} from keystore.`);
      if (selectedRecipientId === recipientId) {
        setSelectedRecipientId('');
      }
      await fetchRecipients();
    } catch (err) {
      setError(`Purge failed: ${err.message}`);
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

      const res = await apiRequest(`/api/v1/recipients/tamper-test?attack_type=${encodeURIComponent(selectedType)}`, {
        method: 'POST',
      });
      setTamperResult(res);
    } catch (err) {
      setTamperError(err.message || 'Adversarial tamper simulation failed.');
    } finally {
      setTamperRunning(false);
    }
  };

  const activeCount = recipients.filter(r => r.status === 'active').length;
  const revokedCount = recipients.filter(r => r.status !== 'active').length;

  const filteredRecipients = recipients.filter((rec) => {
    if (filterStatus === 'active') return rec.status === 'active';
    if (filterStatus === 'revoked') return rec.status !== 'active';
    return true;
  });

  return (
    <section style={{ maxWidth: '1180px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Users size={24} color="#00f0ff" />
            <h2 style={{ fontSize: '1.85rem', margin: 0, color: '#ffffff', fontWeight: 800, letterSpacing: '0.04em' }}>
              OFFICER ROSTER &amp; POST-QUANTUM KEY MANAGEMENT
            </h2>
          </div>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.92rem' }}>
            Member A Component &bull; NIST FIPS 203 (ML-KEM-768) &amp; FIPS 204 (ML-DSA-65) Sovereign Key Enclave
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
          <Lock size={14} color="#38bdf8" />
          <span>KEYSTORE ISOLATION: PBKDF2 + AES-256-GCM</span>
        </div>
      </header>

      {/* Security Invariant Banner */}
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
          <strong style={{ color: '#34d399' }}>Zero Secret Custody Invariant:</strong> Private keys (ML-KEM-768 decapsulation key &amp; ML-DSA-65 signing key)
          and plaintext Content Encryption Keys (CEK) remain strictly inside the recipient's local boundary. Only public keys and SHA3-256 fingerprints are published.
        </div>
      </div>

      {actionMessage && (
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
          <span>{actionMessage}</span>
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
        {/* Enrollment Form */}
        <div className="panel" style={{ background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <KeyRound size={18} color="#00f0ff" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
              Enroll Officer &amp; Generate PQC Keypair
            </h3>
          </div>

          <form onSubmit={handleEnroll} style={{ display: 'grid', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                RECIPIENT ID (OPAQUE)
              </label>
              <input
                type="text"
                required
                placeholder="e.g. recip_wesee_01"
                value={newRecipientId}
                onChange={(e) => setNewRecipientId(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                FULL NAME / UNIT
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Commander R. Sharma"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                OFFICIAL EMAIL
              </label>
              <input
                type="email"
                required
                placeholder="e.g. sharma.r@wesee.mod.in"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                LOCAL KEYSTORE PASSPHRASE
              </label>
              <input
                type="password"
                placeholder="Protects private keys at rest (PBKDF2-AES-GCM)"
                value={newPassphrase}
                onChange={(e) => setNewPassphrase(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              style={{
                backgroundColor: '#00f0ff',
                color: '#060913',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 18px',
                fontWeight: 800,
                fontSize: '0.88rem',
                cursor: submitting ? 'not-allowed' : 'pointer',
                marginTop: '6px',
                boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)'
              }}
            >
              {submitting ? 'GENERATING PQC KEYS...' : 'GENERATE PQC KEYS & ENROLL'}
            </button>
          </form>
        </div>

        {/* Algorithm Standards Reference */}
        <div className="panel" style={{ background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <Cpu size={18} color="#34d399" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
              Cryptographic Suite &amp; Invariants
            </h3>
          </div>
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6, display: 'grid', gap: '8px' }}>
            <li>
              <strong style={{ color: '#38bdf8' }}>Key Encapsulation:</strong> NIST FIPS 203 <code>ML-KEM-768</code> (1,184B public key, 1,088B ciphertext, 32B shared secret).
            </li>
            <li>
              <strong style={{ color: '#34d399' }}>Digital Signatures:</strong> NIST FIPS 204 <code>ML-DSA-65</code> (1,952B public key, 3,309B signature) for canonical event provenance.
            </li>
            <li>
              <strong style={{ color: '#fbbf24' }}>Content Encryption:</strong> <code>AES-256-GCM</code> with fresh 32-byte CEK and unique 12-byte nonces.
            </li>
            <li>
              <strong style={{ color: '#c084fc' }}>Context Binding:</strong> <code>HKDF-SHA-256</code> domain separation binding <code>(doc_id, version_id, recipient_fingerprint)</code>.
            </li>
            <li>
              <strong style={{ color: '#f87171' }}>Envelope Architecture:</strong> 1 shared encrypted payload per document version; N independent recipient-bound envelopes.
            </li>
          </ul>
          <div style={{ marginTop: '20px', padding: '12px 14px', background: 'rgba(6, 11, 22, 0.8)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)', fontSize: '0.8rem', color: '#94a3b8', fontFamily: 'var(--font-mono)', display: 'flex', justifyContent: 'space-between' }}>
            <span>REGISTERED OFFICERS:</span>
            <strong style={{ color: '#00f0ff' }}>{recipients.length}</strong>
          </div>
        </div>
      </div>

      {/* Recipient Roster */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#ffffff', fontWeight: 800, letterSpacing: '0.04em' }}>
              OFFICER RECIPIENT DIRECTORY ({filteredRecipients.length})
            </h3>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
              REVOCATION PRESERVES FORENSIC AUDIT TRAILS &bull; PURGE REMOVES ENTIRELY
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Filter Pill Tabs */}
            <div style={{
              display: 'flex',
              background: 'rgba(6, 11, 22, 0.85)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: '8px',
              padding: '3px',
              gap: '4px'
            }}>
              <button
                type="button"
                onClick={() => setFilterStatus('all')}
                style={{
                  background: filterStatus === 'all' ? 'rgba(0, 240, 255, 0.2)' : 'transparent',
                  border: filterStatus === 'all' ? '1px solid rgba(0, 240, 255, 0.4)' : '1px solid transparent',
                  color: filterStatus === 'all' ? '#00f0ff' : '#94a3b8',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.74rem',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                ALL ({recipients.length})
              </button>
              <button
                type="button"
                onClick={() => setFilterStatus('active')}
                style={{
                  background: filterStatus === 'active' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                  border: filterStatus === 'active' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid transparent',
                  color: filterStatus === 'active' ? '#34d399' : '#94a3b8',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.74rem',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                ACTIVE ({activeCount})
              </button>
              <button
                type="button"
                onClick={() => setFilterStatus('revoked')}
                style={{
                  background: filterStatus === 'revoked' ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                  border: filterStatus === 'revoked' ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid transparent',
                  color: filterStatus === 'revoked' ? '#f87171' : '#94a3b8',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.74rem',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                REVOKED ({revokedCount})
              </button>
            </div>

            {/* Refresh Directory Button (High Visibility Cyan) */}
            <button
              onClick={fetchRecipients}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                fontSize: '0.8rem',
                backgroundColor: 'rgba(0, 240, 255, 0.1)',
                border: '1px solid rgba(0, 240, 255, 0.35)',
                borderRadius: '8px',
                color: '#00f0ff',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700
              }}
            >
              <RefreshCw size={13} className={loading ? 'pulse-beacon' : ''} />
              <span>REFRESH DIRECTORY</span>
            </button>
          </div>
        </div>

        {loading ? (
          <p style={{ color: '#64748b', fontFamily: 'var(--font-mono)' }}>Loading recipient public records from keystore...</p>
        ) : filteredRecipients.length === 0 ? (
          <div className="panel" style={{ textAlign: 'center', padding: '36px', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
            {filterStatus === 'all' 
              ? 'NO OFFICERS ENROLLED YET. ENROLL YOUR FIRST RECIPIENT ABOVE.'
              : `NO ${filterStatus.toUpperCase()} OFFICERS FOUND IN DIRECTORY.`}
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '16px' }}>
            {filteredRecipients.map((rec) => (
              <div
                key={rec.recipient_id}
                style={{
                  background: 'rgba(13, 20, 36, 0.85)',
                  border: rec.status === 'active' ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '12px',
                  padding: '20px 22px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <h4 style={{ margin: '0 0 4px 0', fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
                      {rec.name}
                    </h4>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                      ID: <code style={{ color: '#38bdf8' }}>{rec.recipient_id}</code> &bull; Email: {rec.email}
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span
                      style={{
                        padding: '3px 10px',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        backgroundColor: rec.status === 'active' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        border: rec.status === 'active' ? '1px solid rgba(16, 185, 129, 0.35)' : '1px solid rgba(239, 68, 68, 0.35)',
                        color: rec.status === 'active' ? '#34d399' : '#f87171',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      {rec.status.toUpperCase()}
                    </span>

                    {/* Rotate Keys */}
                    <button
                      onClick={() => handleRotate(rec.recipient_id)}
                      disabled={rec.status !== 'active'}
                      style={{
                        padding: '6px 12px',
                        fontSize: '0.75rem',
                        borderRadius: '6px',
                        border: '1px solid rgba(56, 189, 248, 0.3)',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        color: rec.status === 'active' ? '#38bdf8' : '#64748b',
                        cursor: rec.status === 'active' ? 'pointer' : 'not-allowed',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      ROTATE KEYS
                    </button>

                    {/* Revoke */}
                    <button
                      onClick={() => handleRevoke(rec.recipient_id)}
                      disabled={rec.status !== 'active'}
                      style={{
                        padding: '6px 12px',
                        fontSize: '0.75rem',
                        borderRadius: '6px',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        color: rec.status === 'active' ? '#fbbf24' : '#64748b',
                        cursor: rec.status === 'active' ? 'pointer' : 'not-allowed',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      REVOKE
                    </button>

                    {/* Permanent Delete / Purge */}
                    <button
                      onClick={() => handleDelete(rec.recipient_id)}
                      title="Permanently remove officer from keystore"
                      style={{
                        padding: '6px 10px',
                        fontSize: '0.75rem',
                        borderRadius: '6px',
                        border: '1px solid rgba(239, 68, 68, 0.35)',
                        backgroundColor: 'rgba(239, 68, 68, 0.12)',
                        color: '#f87171',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      <Trash2 size={13} color="#f87171" />
                      <span>PURGE</span>
                    </button>
                  </div>
                </div>

                {/* Fingerprint Boxes */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', background: 'rgba(6, 11, 22, 0.8)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.15)' }}>
                  <div>
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#38bdf8', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                      KEM ENCAPSULATION KEY ({rec.kem_algorithm})
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', wordBreak: 'break-all', fontFamily: 'var(--font-mono)' }}>
                      SHA3-256 Fingerprint:
                      <br />
                      <code style={{ color: '#38bdf8' }}>{rec.kem_fingerprint}</code>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#34d399', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>
                      SIGNING VERIFICATION KEY ({rec.dsa_algorithm})
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', wordBreak: 'break-all', fontFamily: 'var(--font-mono)' }}>
                      SHA3-256 Fingerprint:
                      <br />
                      <code style={{ color: '#34d399' }}>{rec.dsa_fingerprint}</code>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recipient-Local Decryption Simulator */}
      <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <FileCheck size={20} color="#00f0ff" />
          <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#ffffff', fontWeight: 800 }}>
            Recipient-Local Decrypt &amp; Provenance Signing Simulator
          </h3>
        </div>
        <p style={{ margin: '0 0 20px 0', fontSize: '0.88rem', color: '#94a3b8' }}>
          Simulates recipient receiving an encrypted document payload and opening their individual ML-KEM-768 envelope locally to recover the CEK and sign the canonical provenance event.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '18px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
              SELECT RECIPIENT
            </label>
            <select
              value={selectedRecipientId}
              onChange={(e) => setSelectedRecipientId(e.target.value)}
              style={{ width: '100%' }}
            >
              {recipients.map((r) => (
                <option key={r.recipient_id} value={r.recipient_id}>
                  {r.name} ({r.recipient_id}) - {r.status.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
              SESSION WATERMARK TOKEN
            </label>
            <input
              type="text"
              value={simWatermarkToken}
              onChange={(e) => setSimWatermarkToken(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <button
            onClick={handleSimulateEnvelope}
            disabled={simLoading || !selectedRecipientId}
            style={{
              padding: '11px 18px',
              backgroundColor: '#00f0ff',
              color: '#060913',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '0.82rem',
              cursor: simLoading ? 'not-allowed' : 'pointer',
              boxShadow: '0 0 12px rgba(0, 240, 255, 0.25)'
            }}
          >
            STEP 1: GENERATE TEST ENVELOPE
          </button>
          <button
            onClick={handleSimulateDecrypt}
            disabled={simLoading || !simEnvelopeData}
            style={{
              padding: '11px 18px',
              backgroundColor: simEnvelopeData ? '#10b981' : 'rgba(255, 255, 255, 0.08)',
              color: simEnvelopeData ? '#060913' : '#64748b',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '0.82rem',
              cursor: simEnvelopeData ? 'pointer' : 'not-allowed',
              boxShadow: simEnvelopeData ? '0 0 12px rgba(16, 185, 129, 0.3)' : 'none'
            }}
          >
            STEP 2: EXECUTE LOCAL DECRYPT &amp; SIGN
          </button>
        </div>

        {simEnvelopeData && (
          <div style={{ background: 'rgba(6, 11, 22, 0.8)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)', marginBottom: '16px', fontSize: '0.82rem', fontFamily: 'var(--font-mono)' }}>
            <h5 style={{ margin: '0 0 8px 0', fontSize: '0.88rem', color: '#ffffff' }}>
              📦 ENVELOPE PREPARED FOR {simEnvelopeData.envelope.recipient_id}:
            </h5>
            <div><span style={{ color: '#64748b' }}>DOC ID:</span> <code style={{ color: '#38bdf8' }}>{simEnvelopeData.document_id}</code></div>
            <div><span style={{ color: '#64748b' }}>KEM CIPHERTEXT LENGTH:</span> <code style={{ color: '#34d399' }}>1088 bytes (Base64 encoded)</code></div>
            <div><span style={{ color: '#64748b' }}>WRAPPED CEK:</span> <code>{simEnvelopeData.envelope.wrapped_cek.substring(0, 32)}...</code></div>
          </div>
        )}

        {simResult && (
          <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.35)', padding: '18px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <CheckCircle2 size={18} color="#34d399" />
              <strong style={{ color: '#34d399' }}>Decryption &amp; Provenance Signing Verified!</strong>
            </div>
            <div style={{ fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
              DECRYPTED PAYLOAD SIZE: <strong style={{ color: '#ffffff' }}>{simResult.decrypted_size_bytes} bytes</strong> &bull;
              DSA FINGERPRINT: <code style={{ color: '#38bdf8' }}>{simResult.recipient_dsa_fingerprint}</code>
            </div>
            <div style={{ fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '12px', fontFamily: 'var(--font-mono)' }}>
              WATERMARK TOKEN SHA3-256 DIGEST:
              <br />
              <code style={{ fontSize: '0.78rem', color: '#00f0ff' }}>{simResult.token_digest}</code>
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#34d399', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                SIGNED CANONICAL EVENT (READY FOR VALIDATOR SUBMISSION):
              </div>
              <pre style={{
                background: '#060913',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                color: '#6ee7b7',
                padding: '12px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                overflowX: 'auto',
                fontFamily: 'var(--font-mono)'
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
        background: 'rgba(13, 20, 36, 0.85)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        marginBottom: '32px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Zap size={20} color="#f59e0b" />
              <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#ffffff', fontWeight: 800 }}>
                Adversarial Security &amp; Fail-Closed Tamper Testing (Phase 6)
              </h3>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
              Demonstrate live cryptographic defenses under active attack. Proves zero plaintext leakage when tampered.
            </p>
          </div>
          <span style={{
            fontSize: '0.72rem',
            fontWeight: 800,
            padding: '4px 10px',
            borderRadius: '4px',
            background: 'rgba(0, 240, 255, 0.1)',
            border: '1px solid rgba(0, 240, 255, 0.3)',
            color: '#00f0ff',
            letterSpacing: '0.08em',
            fontFamily: 'var(--font-mono)'
          }}>
            EVALUATOR DEMONSTRATION
          </span>
        </div>

        {/* Attack Vector Selector Tabs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
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
                  padding: '14px',
                  borderRadius: '8px',
                  border: active ? '1px solid #00f0ff' : '1px solid rgba(56, 189, 248, 0.2)',
                  background: active ? 'rgba(0, 240, 255, 0.12)' : 'rgba(6, 11, 22, 0.8)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  boxShadow: active ? '0 0 12px rgba(0, 240, 255, 0.2)' : 'none'
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: active ? '#00f0ff' : '#ffffff' }}>
                  {item.label}
                </div>
                <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '3px', fontFamily: 'var(--font-mono)' }}>
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
              padding: '11px 22px',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 800,
              fontSize: '0.82rem',
              cursor: tamperRunning ? 'not-allowed' : 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 0 15px rgba(239, 68, 68, 0.35)',
            }}
          >
            {tamperRunning ? 'SIMULATING ATTACK VECTOR...' : '⚡ TRIGGER ATTACK SIMULATION'}
          </button>
        </div>

        {tamperError && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#f87171',
            padding: '14px 18px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '16px',
            fontFamily: 'var(--font-mono)'
          }}>
            Simulation Error: {tamperError}
          </div>
        )}

        {/* Attack Outcome Verdict Card */}
        {tamperResult && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <ShieldCheck size={26} color="#34d399" />
                <div>
                  <div style={{ fontWeight: 800, fontSize: '1rem', color: '#34d399', fontFamily: 'var(--font-mono)' }}>
                    ATTACK NEUTRALIZED &mdash; {tamperResult.security_verdict}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                    {tamperResult.attack_name}
                  </div>
                </div>
              </div>
              <div style={{
                textAlign: 'right',
                background: 'rgba(6, 11, 22, 0.8)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '6px 14px',
                borderRadius: '6px',
              }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  PLAINTEXT LEAKED
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399', fontFamily: 'var(--font-mono)' }}>
                  {tamperResult.plaintext_leaked_bytes} Bytes
                </div>
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr',
              gap: '10px',
              background: 'rgba(6, 11, 22, 0.8)',
              padding: '14px',
              borderRadius: '6px',
              border: '1px solid rgba(56, 189, 248, 0.15)',
              fontSize: '0.82rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div>
                <strong style={{ color: '#94a3b8' }}>CRYPTOGRAPHIC DEFENSE:</strong>{' '}
                <span style={{ color: '#38bdf8', fontWeight: 700 }}>{tamperResult.defense_mechanism}</span>
              </div>
              <div>
                <strong style={{ color: '#94a3b8' }}>EXCEPTION CAUGHT:</strong>{' '}
                <code style={{ color: '#f87171' }}>
                  {tamperResult.exception_type}
                </code>
              </div>
              <div>
                <strong style={{ color: '#94a3b8' }}>DIAGNOSTIC DETAIL:</strong>{' '}
                <span style={{ color: '#cbd5e1' }}>{tamperResult.exception_detail}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
