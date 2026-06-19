import React from "react";
import SeededWorkflowPage from "./payments/SeededWorkflowPage";

const ROUTE_SEEDED_WORKBENCH = "home";

const DEFAULT_CONFIG = {
  "core.Router": [{ path: ROUTE_SEEDED_WORKBENCH, component: SeededWorkflowPage, rights: [] }],
  "core.MainMenu": [
    {
      name: "PaymentMainMenu",
      text: "Hospital Claim Payment",
      icon: "Receipt",
    },
  ],
  "payment.MainMenu": [{ route: ROUTE_SEEDED_WORKBENCH, text: "Claim to Payment" }],
};

export const PaymentGatewayModule = (cfg) => {
  return { ...DEFAULT_CONFIG, ...cfg };
};
