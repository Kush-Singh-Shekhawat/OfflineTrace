import React, { useState } from 'react';
import { apiRequest } from '../../services/apiClient.js';

export default function InvestigationPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentId, setDocumentId] = useState('doc-suspected-leak-01');
  const [investigatorId, setInvestigatorId] = useState('inv-officer-99');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);

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
    <section style={{ maxWidth: '1080px', margin: '0 auto', fontFamily: 'inherit' }}>
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.8rem', margin: '0 0 6px 0', color: '#0f172a' }}>
          Forensic Watermark Investigation
        </h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: '0.95rem' }}>
          Member B Screen — Suspected PDF analysis, watermark extraction, and cryptographic ledger verification.
        </p>
      </header>

      {/* Honesty & Evidence Boundary Notice */}
      <div style={{
        backgroundColor: '#fffbeb',
        border: '1px solid #fde68a',
        borderRadius: '8px',
        padding: '12px 16px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <span style={{ fontSize: '1.25rem' }}>⚖️</span>
        <div style={{ fontSize: '0.88rem', color: '#92400e', lineHeight: 1.4 }}>
          <strong>Honesty Boundary:</strong> An extracted forensic watermark and valid ledger record links a document to a specific decryption event and recipient cryptographic identity. It does not constitute legal proof of who physically leaked the file.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        {/* Upload Form */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
            📁 Upload Suspected Leaked Document
          </h3>
          <div style={{ display: 'grid', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Select Leaked PDF File
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                style={{ width: '100%', padding: '8px', border: '1px dashed #cbd5e1', borderRadius: '6px' }}
              />
              {selectedFile && (
                <div style={{ fontSize: '0.8rem', color: '#15803d', marginTop: '4px' }}>
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Case / Target Document ID
              </label>
              <input
                type="text"
                value={documentId}
                onChange={(e) => setDocumentId(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                Investigator ID
              </label>
              <input
                type="text"
                value={investigatorId}
                onChange={(e) => setInvestigatorId(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
              />
            </div>

            <button
              onClick={handleUploadAndAnalyze}
              disabled={loading || !selectedFile}
              style={{
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 16px',
                fontWeight: 600,
                cursor: loading || !selectedFile ? 'not-allowed' : 'pointer',
                marginTop: '6px',
              }}
            >
              {loading ? 'Extracting & Verifying...' : '🔍 Analyze Leaked PDF'}
            </button>
          </div>
        </div>

        {/* Quick Simulation Presets */}
        <div className="panel" style={{ padding: '24px', borderRadius: '12px', background: '#ffffff', border: '1px solid #e2e8f0' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.15rem', color: '#1e293b' }}>
            🧪 Quick Test Presets (Phase 5 Gates)
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', margin: '0 0 16px 0' }}>
            Test the investigation verification engine against synthetic fixtures without manual file creation:
          </p>

          <div style={{ display: 'grid', gap: '10px' }}>
            <button
              onClick={() => handleRunPreset('unrelated_clean')}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                background: '#f8fafc',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#0f172a' }}>
                Scenario 1: Unrelated Clean PDF
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                Document has no watermark metadata. Expected: <code>NO_MATCH</code> (confidence 0.0).
              </div>
            </button>

            <button
              onClick={() => handleRunPreset('ambiguous_unregistered')}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                background: '#f8fafc',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#0f172a' }}>
                Scenario 2: Ambiguous / Unregistered Watermark
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                Token extracted from PDF, but no matching block on ledger. Expected: <code>INCONCLUSIVE</code>.
              </div>
            </button>

            <button
              onClick={() => handleRunPreset('sample_leak')}
              disabled={loading}
              style={{
                textAlign: 'left',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                background: '#f8fafc',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#0f172a' }}>
                Scenario 3: Suspected Leak Scan
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                Scans candidate watermark token against local validator chain.
              </div>
            </button>
          </div>
        </div>
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
          <strong>Investigation Error:</strong> {error}
        </div>
      )}

      {/* Investigation Report Display */}
      {report && (
        <div className="panel" style={{
          padding: '28px',
          borderRadius: '12px',
          background: '#ffffff',
          border: '1px solid #cbd5e1',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ margin: '0 0 4px 0', fontSize: '1.3rem', color: '#0f172a' }}>
                Forensic Evidence Report
              </h3>
              <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                ID: <code>{report.investigation_id}</code> &bull; Generated: {new Date(report.generated_at).toLocaleTimeString()}
              </div>
            </div>
            {(() => {
              const badge = getStatusBadge(report.confidence);
              return (
                <span style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  backgroundColor: badge.bg,
                  color: badge.color,
                  border: `1px solid ${badge.border}`,
                }}>
                  {badge.label}
                </span>
              );
            })()}
          </div>

          {/* Diagnostic Summary */}
          <div style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px',
            fontSize: '0.9rem',
            color: '#1e293b',
            lineHeight: 1.5,
          }}>
            <strong>Diagnostics:</strong> {report.diagnostics}
          </div>

          {/* Cryptographic Verification Checklist */}
          <h4 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#334155' }}>
            Cryptographic &amp; Provenance Verification Matrix
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              background: report.signature_verified ? '#f0fdf4' : '#fef2f2',
              border: `1px solid ${report.signature_verified ? '#bbf7d0' : '#fecaca'}`,
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>RECIPIENT SIGNATURE</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: report.signature_verified ? '#15803d' : '#b91c1c', marginTop: '4px' }}>
                {report.signature_verified ? '✅ ML-DSA-65 Valid' : '❌ Unverified'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                Canonical event signed by recipient private key
              </div>
            </div>

            <div style={{
              padding: '16px',
              borderRadius: '8px',
              background: report.quorum_verified ? '#f0fdf4' : '#fef2f2',
              border: `1px solid ${report.quorum_verified ? '#bbf7d0' : '#fecaca'}`,
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>QUORUM COMMIT</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: report.quorum_verified ? '#15803d' : '#b91c1c', marginTop: '4px' }}>
                {report.quorum_verified ? '✅ 2-of-3 Quorum' : '❌ No Quorum'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                Independent validator signatures committed block
              </div>
            </div>

            <div style={{
              padding: '16px',
              borderRadius: '8px',
              background: report.chain_verified ? '#f0fdf4' : '#fef2f2',
              border: `1px solid ${report.chain_verified ? '#bbf7d0' : '#fecaca'}`,
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>HASH CHAIN</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: report.chain_verified ? '#15803d' : '#b91c1c', marginTop: '4px' }}>
                {report.chain_verified ? '✅ Chain Continuous' : '❌ Diverged'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                SHA3-256 block sequence uncorrupted
              </div>
            </div>
          </div>

          <button
            onClick={downloadReport}
            style={{
              padding: '10px 18px',
              backgroundColor: '#1e293b',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            💾 Export Evidence Report (JSON)
          </button>
        </div>
      )}
    </section>
  );
}
