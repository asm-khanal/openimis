import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useHistory } from "@openimis/fe-core";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

const CLAIM_STATUS_MAP = {
  1: { label: "Entered", color: "warning" },
  16: { label: "Valuated", color: "success" },
  32: { label: "Rejected", color: "error" },
};

const BATCH_STATUS_MAP = {
  1: { label: "Pending Approval", color: "warning" },
  2: { label: "Approved", color: "info" },
  3: { label: "Processing", color: "primary" },
  4: { label: "Paid", color: "success" },
  5: { label: "Partially Paid", color: "secondary" },
  6: { label: "Failed", color: "error" },
  7: { label: "Rejected", color: "error" },
};

const SEED_TEMPLATES = [
  {
    id: "hf001",
    label: "HF001 - CHF 1000000001 - A00",
    health_facility_code: "HF001",
    insuree_chf_id: "1000000001",
    diagnosis_code: "A00",
    date_from: "2026-06-01",
    date_to: "2026-06-02",
    items: [{ item_code: "ITM001", qty_claimed: 2, price_claimed: "25.00" }],
    services: [{ service_code: "SVC001", qty_claimed: 1, price_claimed: "200.00" }],
  },
  {
    id: "hf002",
    label: "HF002 - CHF 1000000002 - A01",
    health_facility_code: "HF002",
    insuree_chf_id: "1000000002",
    diagnosis_code: "A01",
    date_from: "2026-06-03",
    date_to: "2026-06-04",
    items: [{ item_code: "ITM002", qty_claimed: 1, price_claimed: "80.00" }],
    services: [
      { service_code: "SVC003", qty_claimed: 1, price_claimed: "300.00" },
      { service_code: "SVC007", qty_claimed: 1, price_claimed: "150.00" },
    ],
  },
  {
    id: "hf008",
    label: "HF008 - CHF 1000000008 - A09",
    health_facility_code: "HF008",
    insuree_chf_id: "1000000008",
    diagnosis_code: "A09",
    date_from: "2026-06-05",
    date_to: "2026-06-06",
    items: [{ item_code: "ITM003", qty_claimed: 2, price_claimed: "45.00" }],
    services: [{ service_code: "SVC006", qty_claimed: 1, price_claimed: "400.00" }],
  },
];

function getAuthHeaders() {
  const cookies = document.cookie.split("; ");
  const csrfCookie = cookies.find((c) => c.startsWith("csrftoken"));
  const csrfToken = csrfCookie?.split("=")[1];
  const headers = { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" };
  if (csrfToken) headers["X-CSRFToken"] = csrfToken;
  return headers;
}

function formatAmount(value) {
  return Number(value || 0).toLocaleString();
}

const SeededWorkflowPage = () => {
  const history = useHistory();
  const [templateId, setTemplateId] = useState(SEED_TEMPLATES[0].id);
  const [claims, setClaims] = useState([]);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  const selectedTemplate = useMemo(
    () => SEED_TEMPLATES.find((template) => template.id === templateId) || SEED_TEMPLATES[0],
    [templateId],
  );

  const claimPayload = useMemo(
    () => ({
      health_facility_code: selectedTemplate.health_facility_code,
      insuree_chf_id: selectedTemplate.insuree_chf_id,
      diagnosis_code: selectedTemplate.diagnosis_code,
      date_from: selectedTemplate.date_from,
      date_to: selectedTemplate.date_to,
      items: selectedTemplate.items,
      services: selectedTemplate.services,
    }),
    [selectedTemplate],
  );

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [claimsResp, batchesResp] = await Promise.all([
        fetch(`${window.location.origin}/api/claims/`, { headers: getAuthHeaders() }),
        fetch(`${window.location.origin}/api/payment_batches/`, { headers: getAuthHeaders() }),
      ]);
      if (!claimsResp.ok) throw new Error(`Claims request failed: HTTP ${claimsResp.status}`);
      if (!batchesResp.ok) throw new Error(`Batch request failed: HTTP ${batchesResp.status}`);
      setClaims(await claimsResp.json());
      setBatches(await batchesResp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const postJson = async (url, body) => {
    const resp = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    const data = await resp.json().catch(() => null);
    if (!resp.ok) {
      const message = data?.error || data?.detail || `HTTP ${resp.status}`;
      throw new Error(message);
    }
    return data;
  };

  const withBusy = async (action) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await action();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleCreateClaim = () =>
    withBusy(async () => {
      await postJson(`${window.location.origin}/api/claims/`, claimPayload);
      setNotice(`Claim created for ${selectedTemplate.health_facility_code} and ${selectedTemplate.insuree_chf_id}.`);
      await fetchData();
    });

  const handleValuateClaim = (claimId) =>
    withBusy(async () => {
      await postJson(`${window.location.origin}/api/claims/${claimId}/valuate/`, {});
      setNotice("Claim valuated.");
      await fetchData();
    });

  const handleCreateBatch = (healthFacilityCode) =>
    withBusy(async () => {
      const data = await postJson(`${window.location.origin}/api/payment_batches/`, {
        health_facility_codes: [healthFacilityCode],
      });
      setNotice(
        Array.isArray(data) && data.length
          ? "Payment batch created."
          : "No valuated claims available for batch creation.",
      );
      await fetchData();
    });

  const handleApproveBatch = (batchId) =>
    withBusy(async () => {
      await postJson(`${window.location.origin}/api/payment_batches/approve/`, {
        batch_ids: [batchId],
      });
      setNotice("Batch approved.");
      await fetchData();
    });

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, alignItems: "flex-start", mb: 2 }}>
        <Box>
          <Typography variant="h5">Seeded Claim Workbench</Typography>
          <Typography variant="body2" color="text.secondary">
            Uses fixed seeded codes only. No lookup endpoints are required.
          </Typography>
        </Box>
        <Button variant="outlined" onClick={fetchData} disabled={busy}>
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {notice && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {notice}
        </Alert>
      )}

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, alignItems: "center", mb: 1 }}>
            <Box>
              <Typography variant="h6">Create Fixed Claim</Typography>
              <Typography variant="body2" color="text.secondary">
                Template: {selectedTemplate.label}
              </Typography>
            </Box>
            <Button variant="contained" onClick={handleCreateClaim} disabled={busy}>
              Create Claim
            </Button>
          </Box>
          <Select fullWidth value={templateId} onChange={(e) => setTemplateId(e.target.value)} disabled={busy}>
            {SEED_TEMPLATES.map((template) => (
              <MenuItem key={template.id} value={template.id}>
                {template.label}
              </MenuItem>
            ))}
          </Select>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, 1fr)" }, gap: 2 }}>
            <TextField
              label="Health Facility"
              value={claimPayload.health_facility_code}
              InputProps={{ readOnly: true }}
            />
            <TextField label="Insuree CHF ID" value={claimPayload.insuree_chf_id} InputProps={{ readOnly: true }} />
            <TextField label="Diagnosis" value={claimPayload.diagnosis_code} InputProps={{ readOnly: true }} />
            <TextField label="Date From" value={claimPayload.date_from} InputProps={{ readOnly: true }} />
          </Box>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Items:{" "}
              {claimPayload.items
                .map((item) => `${item.item_code} x${item.qty_claimed} @ ${item.price_claimed}`)
                .join(", ")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Services:{" "}
              {claimPayload.services
                .map((service) => `${service.service_code} x${service.qty_claimed} @ ${service.price_claimed}`)
                .join(", ")}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      <Typography variant="h6" gutterBottom>
        Claims
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Code</TableCell>
              <TableCell>Facility</TableCell>
              <TableCell>CHF ID</TableCell>
              <TableCell align="right">Claimed</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {claims.map((claim) => (
              <TableRow key={claim.id}>
                <TableCell>{claim.code}</TableCell>
                <TableCell>{claim.health_facility_code || "-"}</TableCell>
                <TableCell>{claim.insuree_chf_id || "-"}</TableCell>
                <TableCell align="right">{formatAmount(claim.claimed)}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={claim.status_display || CLAIM_STATUS_MAP[claim.status]?.label || "Unknown"}
                    color={CLAIM_STATUS_MAP[claim.status]?.color || "default"}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                    {claim.status === 1 && (
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => handleValuateClaim(claim.id)}
                        disabled={busy}
                      >
                        Valuate
                      </Button>
                    )}
                    {claim.status === 16 && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleCreateBatch(claim.health_facility_code)}
                        disabled={busy}
                      >
                        Create Batch
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {claims.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No claims created yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" gutterBottom>
        Payment Batches
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Batch Code</TableCell>
              <TableCell>Facility</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell align="right">Claims</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {batches.map((batch) => (
              <TableRow
                key={batch.id}
                hover
                sx={{ cursor: "pointer" }}
                onClick={() => history.push(`/payment_batches/${batch.id}`)}
              >
                <TableCell>{batch.batch_code}</TableCell>
                <TableCell>{batch.health_facility_code || batch.health_facility_name || "-"}</TableCell>
                <TableCell align="right">{formatAmount(batch.total_amount)}</TableCell>
                <TableCell align="right">{batch.total_claims}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={batch.status_display || BATCH_STATUS_MAP[batch.status]?.label || "Unknown"}
                    color={BATCH_STATUS_MAP[batch.status]?.color || "default"}
                  />
                </TableCell>
                <TableCell>
                  {batch.status === 1 && (
                    <Button
                      size="small"
                      variant="contained"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleApproveBatch(batch.id);
                      }}
                      disabled={busy}
                    >
                      Approve
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {batches.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No payment batches yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default SeededWorkflowPage;
