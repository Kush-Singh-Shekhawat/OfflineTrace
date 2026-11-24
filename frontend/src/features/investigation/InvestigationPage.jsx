import React, { useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';
import { SearchCheck, ShieldCheck, AlertTriangle, CheckCircle2, FileCheck } from '../../components/Icons.jsx';

export default function InvestigationPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentId, setDocumentId] = useState('doc-suspected-leak-01');
  const [investigatorId, setInvestigatorId] = useState('inv-officer-99');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);

  // Court of Inquiry Dossier modal state
  const [dossierModal, setDossierModal] = useState(false);
  const [dossierLoading, setDossierLoading] = useState(false);
  const [dossierData, setDossierData] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select a PDF file to analyze.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setReport(null);

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('document_id', documentId);
      formData.append('investigator_id', investigatorId);

      const res = await apiRequest('/api/v1/investigations', {
        method: 'POST',
        body: formData,
      });
      setReport(res);
    } catch (err) {
      setError(`Investigation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPreset = async (presetType) => {
    try {
      setLoading(true);
      setError(null);
      setReport(null);

      // 1. Fetch synthetic PDF preset
      const presetData = await apiRequest(`/api/v1/investigations/simulate-preset?preset_type=${presetType}`, {
        method: 'POST',
      });

      // 2. Submit for analysis
      const res = await apiRequest('/api/v1/investigations/analyze-base64', {
        method: 'POST',
        body: JSON.stringify({
          document_id: `preset-${presetType}`,
          investigator_id: investigatorId,
          pdf_base64: presetData.pdf_base64,
        }),
      });
      setReport(res);
    } catch (err) {
      setError(`Preset investigation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Forensic_Report_${report.investigation_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFetchDossier = async () => {
    if (!report) return;
    try {
      setDossierLoading(true);
      const data = await apiRequest(`/api/v1/investigations/${report.investigation_id}/dossier`);
      setDossierData(data);
      setDossierModal(true);
    } catch (err) {
      alert(`Failed to compile Court of Inquiry dossier: ${err.message}`);
    } finally {
      setDossierLoading(false);
    }
  };

  const downloadDossierJson = () => {
    if (!dossierData) return;
    const blob = new Blob([JSON.stringify(dossierData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${dossierData.dossier_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusBadge = (confidence) => {
    if (confidence >= 0.95) {
      return { label: 'EXACT MATCH (100%)', color: '#15803d', bg: '#dcfce7', border: '#86efac' };
    } else if (confidence >= 0.70) {
      return { label: 'LIKELY MATCH', color: '#1d4ed8', bg: '#dbeafe', border: '#93c5fd' };
    } else if (confidence > 0.0) {
      return { label: 'INCONCLUSIVE', color: '#b45309', bg: '#fef3c7', border: '#fcd34d' };
    } else {
      return { label: 'NO MATCH (0%)', color: '#b91c1c', bg: '#fee2e2', border: '#fca5a5' };
    }
  };

  return (
    <section style={{ maxWidth: '1180px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <SearchCheck size={24} color="#00f0ff" />
            <h2 style={{ fontSize: '1.85rem', margin: 0, color: '#ffffff', fontWeight: 800, letterSpacing: '0.04em' }}>
              FORENSIC WATERMARK INVESTIGATION
            </h2>
          </div>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.92rem' }}>
            Member B Component &bull; Suspected PDF Leak Analysis, Non-Blind Extraction, and Ledger Quorum Verification
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
          <ShieldCheck size={14} color="#38bdf8" />
          <span>FORENSIC PROFILE: METADATA FEC (3X REPETITION)</span>
        </div>
      </header>

      {/* Honesty & Evidence Boundary Notice */}
      <div style={{
        background: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '26px',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
      }}>
        <span style={{ fontSize: '1.4rem' }}>⚖️</span>
        <div style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.5 }}>
          <strong style={{ color: '#fbbf24' }}>Forensic Invariant Boundary:</strong> An extracted forensic watermark and valid ledger record links a document to a specific decryption event and recipient cryptographic identity. It does not constitute standalone legal proof of who physically leaked the file.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Upload Form */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
            📁 Upload Suspected Leaked Document
          </h3>
          <div style={{ display: 'grid', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                SELECT LEAKED PDF FILE
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                style={{ width: '100%', padding: '10px', fontSize: '0.82rem' }}
              />
              {selectedFile && (
                <div style={{ fontSize: '0.76rem', color: '#34d399', marginTop: '6px', fontFamily: 'var(--font-mono)' }}>
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                TARGET DOCUMENT ID
              </label>
              <input
                type="text"
                value={documentId}
                onChange={(e) => setDocumentId(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#94a3b8', marginBottom: '6px', fontFamily: 'var(--font-mono)' }}>
                INVESTIGATOR IDENTIFIER
              </label>
              <input
                type="text"
                value={investigatorId}
                onChange={(e) => setInvestigatorId(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>

            <button
              onClick={handleUploadAndAnalyze}
              disabled={loading || !selectedFile}
              style={{
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 18px',
                fontWeight: 800,
                fontSize: '0.85rem',
                cursor: loading || !selectedFile ? 'not-allowed' : 'pointer',
                marginTop: '6px',
                boxShadow: '0 0 15px rgba(239, 68, 68, 0.35)',
              }}
            >
              {loading ? 'EXTRACTING & VERIFYING...' : '🔍 ANALYZE LEAKED PDF'}
            </button>
          </div>
        </div>

        {/* Quick Simulation Presets */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: 'rgba(13, 20, 36, 0.85)', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1.15rem', color: '#ffffff', fontWeight: 700 }}>
            🧪 Quick Test Presets (Phase 5 Verification Gates)
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 16px 0' }}>
            Test the investigation verification engine against synthetic fixtures without manual file creation:
          </p>

          <div style={{ display: 'grid', gap: '10px' }}>
            <button
              onClick={() => handleRunPreset('unrelated_clean')}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                background: 'rgba(6, 11, 22, 0.8)',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#ffffff' }}>
                Scenario 1: Unrelated Clean PDF
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                Document has no watermark metadata. Expected: <code style={{ color: '#f87171' }}>NO_MATCH</code> (0.0).
              </div>
            </button>

            <button
              onClick={() => handleRunPreset('ambiguous_unregistered')}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                background: 'rgba(6, 11, 22, 0.8)',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#ffffff' }}>
                Scenario 2: Ambiguous / Unregistered Watermark
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                Token extracted from PDF, but no matching block on ledger. Expected: <code style={{ color: '#fbbf24' }}>INCONCLUSIVE</code>.
              </div>
            </button>

            <button
              onClick={() => handleRunPreset('sample_leak')}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                background: 'rgba(6, 11, 22, 0.8)',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#ffffff' }}>
                Scenario 3: Suspected Leak Scan
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                Scans candidate watermark token against local validator chain.
              </div>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '10px',
          padding: '14px 18px',
          marginBottom: '22px',
          color: '#f87171',
          fontSize: '0.9rem',
          fontFamily: 'var(--font-mono)'
        }}>
          <strong>Investigation Error:</strong> {error}
        </div>
      )}

      {/* Investigation Report Display */}
      {report && (
        <div className="panel" style={{
          padding: '28px',
          borderRadius: '12px',
          background: 'rgba(13, 20, 36, 0.85)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '1.3rem', color: '#ffffff', fontWeight: 800 }}>
                Forensic Evidence Report
              </h3>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                ID: <code style={{ color: '#00f0ff' }}>{report.investigation_id}</code> &bull; Generated: {new Date(report.generated_at).toLocaleTimeString()}
              </div>
            </div>
            {(() => {
              const badge = getStatusBadge(report.confidence);
              return (
                <span style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  fontWeight: 800,
                  backgroundColor: badge.bg,
                  color: badge.color,
                  border: `1px solid ${badge.border}`,
                  fontFamily: 'var(--font-mono)'
                }}>
                  {badge.label}
                </span>
              );
            })()}
          </div>

          {/* Diagnostic Summary */}
          <div style={{
            background: 'rgba(6, 11, 22, 0.8)',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px',
            fontSize: '0.88rem',
            color: '#cbd5e1',
            lineHeight: 1.5,
            fontFamily: 'var(--font-mono)'
          }}>
            <strong style={{ color: '#38bdf8' }}>DIAGNOSTICS:</strong> {report.diagnostics}
          </div>

          {/* Cryptographic Verification Checklist */}
          <h4 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#ffffff', fontWeight: 700 }}>
            Cryptographic &amp; Provenance Verification Matrix
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              background: report.signature_verified ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
              border: `1px solid ${report.signature_verified ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>RECIPIENT SIGNATURE</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: report.signature_verified ? '#34d399' : '#f87171', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {report.signature_verified ? 'ML-DSA-65 VALID' : 'UNVERIFIED'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>
                Canonical event signed by recipient private key
              </div>
            </div>

            <div style={{
              padding: '16px',
              borderRadius: '8px',
              background: report.quorum_verified ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
              border: `1px solid ${report.quorum_verified ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>QUORUM COMMIT</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: report.quorum_verified ? '#34d399' : '#f87171', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {report.quorum_verified ? '2-OF-3 QUORUM' : 'NO QUORUM'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>
                Independent validator signatures committed block
              </div>
            </div>

            <div style={{
              padding: '16px',
              borderRadius: '8px',
              background: report.chain_verified ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
              border: `1px solid ${report.chain_verified ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>HASH CHAIN</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: report.chain_verified ? '#34d399' : '#f87171', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {report.chain_verified ? 'CHAIN CONTINUOUS' : 'DIVERGED'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>
                SHA3-256 block sequence uncorrupted
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <button
              onClick={handleFetchDossier}
              disabled={dossierLoading}
              style={{
                padding: '12px 20px',
                backgroundColor: '#00f0ff',
                color: '#060913',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 800,
                fontSize: '0.82rem',
                cursor: dossierLoading ? 'not-allowed' : 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 0 15px rgba(0, 240, 255, 0.3)',
                fontFamily: 'var(--font-mono)'
              }}
            >
              {dossierLoading ? 'COMPILING DOSSIER...' : '🏛️ GENERATE COURT OF INQUIRY DOSSIER'}
            </button>

            <button
              onClick={downloadReport}
              style={{
                padding: '12px 18px',
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                color: '#ffffff',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '0.82rem',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)'
              }}
            >
              💾 EXPORT EVIDENCE SUMMARY (JSON)
            </button>
          </div>
        </div>
      )}


      {/* Court of Inquiry Dossier Modal */}
      {dossierModal && dossierData && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px',
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '12px',
            maxWidth: '850px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '32px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '2px solid #cbd5e1',
          }}>
            {/* Dossier Military Heading */}
            <div style={{ borderBottom: '2px solid #0f172a', paddingBottom: '16px', marginBottom: '20px', textAlign: 'center' }}>
              <div style={{
                display: 'inline-block',
                background: '#dc2626',
                color: '#ffffff',
                fontWeight: 800,
                fontSize: '0.75rem',
                padding: '2px 10px',
                borderRadius: '4px',
                letterSpacing: '0.1em',
                marginBottom: '8px',
              }}>
                {dossierData.classification}
              </div>
              <h2 style={{ margin: '4px 0', fontSize: '1.4rem', color: '#0f172a', letterSpacing: '0.02em' }}>
                COURT OF INQUIRY FORENSIC ATTRIBUTION DOSSIER
              </h2>
              <div style={{ fontSize: '0.85rem', color: '#475569', fontWeight: 600 }}>
                {dossierData.authority} &bull; {dossierData.jurisdiction}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                Dossier Identifier: <code>{dossierData.dossier_id}</code> | Time of Generation: {dossierData.generated_at}
              </div>
            </div>

            {/* Verdict Box */}
            <div style={{
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
                  Forensic Attribution Verdict
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                  {dossierData.forensic_verdict} (Confidence: {(dossierData.confidence_score * 100).toFixed(0)}%)
                </div>
                <div style={{ fontSize: '0.82rem', color: '#334155', marginTop: '4px' }}>
                  {dossierData.diagnostics}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{
                  display: 'inline-block',
                  padding: '6px 14px',
                  borderRadius: '999px',
                  background: dossierData.confidence_score >= 0.95 ? '#dcfce7' : '#fef3c7',
                  color: dossierData.confidence_score >= 0.95 ? '#15803d' : '#b45309',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                }}>
                  {dossierData.confidence_score >= 0.95 ? 'ATTRIBUTION CONFIRMED' : 'FURTHER INQUIRY REQUIRED'}
                </span>
              </div>
            </div>

            {/* Evidence & Attributed Recipient Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#1e293b' }}>
                  👤 Attributed Recipient Credentials
                </h4>
                <div style={{ fontSize: '0.82rem', color: '#334155', display: 'grid', gap: '6px' }}>
                  <div><strong>Recipient ID:</strong> <code>{dossierData.cryptographic_proof_matrix.attributed_recipient.recipient_id}</code></div>
                  <div><strong>Name / Unit:</strong> {dossierData.cryptographic_proof_matrix.attributed_recipient.name_or_unit}</div>
                  <div><strong>PQC Signature Algorithm:</strong> {dossierData.cryptographic_proof_matrix.attributed_recipient.dsa_algorithm}</div>
                  <div><strong>DSA Key Fingerprint:</strong> <br/><code style={{ fontSize: '0.75rem' }}>{dossierData.cryptographic_proof_matrix.attributed_recipient.dsa_public_fingerprint || 'N/A'}</code></div>
                </div>
              </div>

              <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#1e293b' }}>
                  🏛️ Consensus &amp; Immutable Ledger Proof
                </h4>
                <div style={{ fontSize: '0.82rem', color: '#334155', display: 'grid', gap: '6px' }}>
                  <div><strong>Consensus Quorum:</strong> {dossierData.cryptographic_proof_matrix.consensus_quorum.consensus_model}</div>
                  <div><strong>Validators Signed:</strong> {dossierData.cryptographic_proof_matrix.consensus_quorum.validators_committed.join(', ')}</div>
                  <div><strong>Committed Block ID:</strong> <code>{dossierData.cryptographic_proof_matrix.immutable_ledger.block_id}</code> (Seq: {dossierData.cryptographic_proof_matrix.immutable_ledger.block_sequence})</div>
                  <div><strong>Block Hash:</strong> <br/><code style={{ fontSize: '0.75rem' }}>{dossierData.cryptographic_proof_matrix.immutable_ledger.block_hash}</code></div>
                </div>
              </div>
            </div>

            {/* Digital Seal */}
            <div style={{
              background: '#042f2e',
              color: '#a7f3d0',
              padding: '14px 18px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '0.8rem',
            }}>
              <div style={{ fontWeight: 700, color: '#34d399', marginBottom: '4px' }}>
                🔒 SHA3-256 Tamper-Evident Digital Seal:
              </div>
              <code style={{ fontSize: '0.78rem', wordBreak: 'break-all' }}>
                {dossierData.digital_seal_sha3_256}
              </code>
              <div style={{ fontSize: '0.72rem', color: '#6ee7b7', marginTop: '4px' }}>
                {dossierData.admissibility_statement}
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => window.print()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#0284c7',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                🖨️ Print Formal Dossier
              </button>
              <button
                onClick={downloadDossierJson}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#0f172a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                💾 Download Sealed JSON
              </button>
              <button
                onClick={() => setDossierModal(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f1f5f9',
                  color: '#475569',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
