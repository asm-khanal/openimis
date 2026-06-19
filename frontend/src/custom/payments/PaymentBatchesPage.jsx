import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "@openimis/fe-core";
import {
  Chip,
  Button,
  Typography,
  Box,
  Paper,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

const STATUS_MAP = {
  1: { label: "Pending Approval", color: "warning" },
  2: { label: "Approved", color: "info" },
  3: { label: "Processing", color: "primary" },
  4: { label: "Paid", color: "success" },
  5: { label: "Partially Paid", color: "secondary" },
  6: { label: "Failed", color: "error" },
  7: { label: "Rejected", color: "error" },
};

function getAuthHeaders() {
  const cookies = document.cookie.split("; ");
  const csrfCookie = cookies.find((c) => c.startsWith("csrftoken"));
  const csrfToken = csrfCookie?.split("=")[1];
  const headers = { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" };
  if (csrfToken) headers["X-CSRFToken"] = csrfToken;
  return headers;
}

const PaymentBatchesPage = () => {
  const history = useHistory();
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBatches = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${window.location.origin}/api/payment_batches/`, { headers: getAuthHeaders() });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      setBatches(await resp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  const handleApprove = async (batchId) => {
    try {
      const resp = await fetch(`${window.location.origin}/api/payment_batches/approve/`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ batch_ids: [batchId] }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchBatches();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading)
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Box>
          <Typography variant="h5">Payment Batches</Typography>
          <Typography variant="body2" color="text.secondary">
            Batches are created from valuated claims by the backend.
          </Typography>
        </Box>
        <Button variant="outlined" onClick={fetchBatches}>
          Refresh
        </Button>
      </Box>
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error: {error}
        </Typography>
      )}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Batch Code</TableCell>
              <TableCell>Health Facility</TableCell>
              <TableCell align="right">Total Amount</TableCell>
              <TableCell align="right">Claims</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {batches.map((b) => (
              <TableRow
                key={b.id}
                hover
                sx={{ cursor: "pointer" }}
                onClick={() => history.push(`/payment_batches/${b.id}`)}
              >
                <TableCell>{b.batch_code}</TableCell>
                <TableCell>{b.health_facility_name || b.health_facility_code || "-"}</TableCell>
                <TableCell align="right">{Number(b.total_amount).toLocaleString()}</TableCell>
                <TableCell align="right">{b.total_claims}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={b.status_display || STATUS_MAP[b.status]?.label || "Unknown"}
                    color={STATUS_MAP[b.status]?.color || "default"}
                  />
                </TableCell>
                <TableCell>{b.created_at ? new Date(b.created_at).toLocaleDateString() : "-"}</TableCell>
                <TableCell>
                  {b.status === 1 && (
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleApprove(b.id);
                      }}
                    >
                      Approve
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {batches.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No payment batches found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default PaymentBatchesPage;
