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
  Grid,
  Card,
  CardContent,
} from "@mui/material";
import { ArrowBack } from "@mui/icons-material";

const BATCH_STATUS_MAP = {
  1: { label: "Pending Approval", color: "warning" },
  2: { label: "Approved", color: "info" },
  3: { label: "Processing", color: "primary" },
  4: { label: "Paid", color: "success" },
  5: { label: "Partially Paid", color: "secondary" },
  6: { label: "Failed", color: "error" },
  7: { label: "Rejected", color: "error" },
};

const CLAIM_STATUS_MAP = {
  1: { label: "Pending", color: "warning" },
  2: { label: "Paid", color: "success" },
  3: { label: "Failed", color: "error" },
  4: { label: "Excluded", color: "default" },
};

function getAuthHeaders() {
  const cookies = document.cookie.split("; ");
  const csrfCookie = cookies.find((c) => c.startsWith("csrftoken"));
  const csrfToken = csrfCookie?.split("=")[1];
  const headers = { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" };
  if (csrfToken) headers["X-CSRFToken"] = csrfToken;
  return headers;
}

const PaymentBatchDetailPage = ({ match }) => {
  const history = useHistory();
  const [batch, setBatch] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const batchId = match?.params?.id;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [batchResp, recordsResp] = await Promise.all([
        fetch(`${window.location.origin}/api/payment_batches/${batchId}/`, { headers: getAuthHeaders() }),
        fetch(`${window.location.origin}/api/payment_records/?payment_batch=${batchId}`, { headers: getAuthHeaders() }),
      ]);
      if (!batchResp.ok) throw new Error(`HTTP ${batchResp.status}`);
      setBatch(await batchResp.json());
      if (recordsResp.ok) setRecords(await recordsResp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  useEffect(() => {
    if (batchId) fetchData();
  }, [batchId, fetchData]);

  if (loading)
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  if (error)
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">Error: {error}</Typography>
      </Box>
    );
  if (!batch)
    return (
      <Box sx={{ p: 2 }}>
        <Typography>Batch not found</Typography>
      </Box>
    );

  return (
    <Box sx={{ p: 2 }}>
      <Button startIcon={<ArrowBack />} onClick={() => history.push("/payment_batches")} sx={{ mb: 2 }}>
        Back
      </Button>
      <Typography variant="h5" gutterBottom>
        Payment Batch: {batch.batch_code}
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="caption">
                Health Facility
              </Typography>
              <Typography variant="body1">{batch.health_facility_name || batch.health_facility_code || "-"}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="caption">
                Total Amount
              </Typography>
              <Typography variant="h6">{Number(batch.total_amount).toLocaleString()}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="caption">
                Claims
              </Typography>
              <Typography variant="h6">{batch.total_claims}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="caption">
                Status
              </Typography>
              <Chip
                label={batch.status_display || BATCH_STATUS_MAP[batch.status]?.label || "Unknown"}
                color={BATCH_STATUS_MAP[batch.status]?.color || "default"}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="caption">
                Approved Date
              </Typography>
              <Typography variant="body1">
                {batch.approved_date ? new Date(batch.approved_date).toLocaleString() : "-"}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="caption">
                Paid Date
              </Typography>
              <Typography variant="body1">
                {batch.paid_date ? new Date(batch.paid_date).toLocaleString() : "-"}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Claims in Batch
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Claim Code</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Payment Reference</TableCell>
              <TableCell>Failure Reason</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(batch.batch_claims || []).map((c) => (
              <TableRow key={c.id}>
                <TableCell>{c.claim_code}</TableCell>
                <TableCell align="right">{Number(c.amount).toLocaleString()}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={CLAIM_STATUS_MAP[c.status]?.label || "Unknown"}
                    color={CLAIM_STATUS_MAP[c.status]?.color || "default"}
                  />
                </TableCell>
                <TableCell>{c.payment_reference || "-"}</TableCell>
                <TableCell>{c.failure_reason || "-"}</TableCell>
              </TableRow>
            ))}
            {(batch.batch_claims || []).length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No claims in this batch
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {records.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>
            Payment Records
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Payment Reference</TableCell>
                  <TableCell align="right">Amount Paid</TableCell>
                  <TableCell align="right">Claims Paid</TableCell>
                  <TableCell align="right">Claims Failed</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {records.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.payment_api_reference || "-"}</TableCell>
                    <TableCell align="right">{Number(r.total_paid_amount).toLocaleString()}</TableCell>
                    <TableCell align="right">{r.claims_paid_count}</TableCell>
                    <TableCell align="right">{r.claims_failed_count}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={r.status}
                        color={
                          r.status === "PAID" || r.status === "RECEIVED"
                            ? "success"
                            : r.status === "FAILED"
                            ? "error"
                            : "default"
                        }
                      />
                    </TableCell>
                    <TableCell>{r.received_date ? new Date(r.received_date).toLocaleString() : "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
      {records.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No payment records have been received for this batch yet.
        </Typography>
      )}
    </Box>
  );
};

export default PaymentBatchDetailPage;
