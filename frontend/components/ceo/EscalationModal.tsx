"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock, DollarSign, User, Package } from "lucide-react";

interface EscalationData {
  id: string;
  order_id: string;
  vendor_id?: string;
  amount?: number;
  reason?: string;
  title: string;
  message: string;
}

interface EscalationModalProps {
  escalation: EscalationData | null;
  onClose: () => void;
  onViewDetails: (orderId: string) => void;
}

export function EscalationModal({ escalation, onClose, onViewDetails }: EscalationModalProps) {
  const router = useRouter();
  const [countdown, setCountdown] = useState(15); // Auto-close after 15 seconds

  useEffect(() => {
    if (!escalation) return;

    // Start countdown
    setCountdown(15);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [escalation]);

  if (!escalation) return null;

  const getReasonBadge = (reason?: string) => {
    switch (reason) {
      case "HIGH_VALUE":
        return (
          <Badge variant="destructive" className="text-xs">
            <DollarSign className="h-3 w-3 mr-1" />
            High-Value Transaction
          </Badge>
        );
      case "VENDOR_FLAGGED":
        return (
          <Badge variant="outline" className="text-xs border-orange-500 text-orange-700 dark:text-orange-400">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Vendor Flagged
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="text-xs">
            <Package className="h-3 w-3 mr-1" />
            Requires Review
          </Badge>
        );
    }
  };

  const handleViewDetails = () => {
    onClose();
    onViewDetails(escalation.order_id);
  };

  const formatAmount = (amount?: number) => {
    if (!amount) return "N/A";
    return `₦${amount.toLocaleString()}`;
  };

  return (
    <Dialog open={!!escalation} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md border-l-4 border-l-red-500">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <AlertTriangle className="h-5 w-5" />
            {escalation.title}
          </DialogTitle>
          <DialogDescription className="text-slate-600 dark:text-slate-400">
            {escalation.message}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Order Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground uppercase">Order ID</p>
              <p className="font-mono text-sm font-medium text-slate-900 dark:text-white">
                #{escalation.order_id.slice(0, 12)}...
              </p>
            </div>
            {escalation.amount && (
              <div>
                <p className="text-xs text-muted-foreground uppercase">Amount</p>
                <p className="text-sm font-bold text-red-600 dark:text-red-400">
                  {formatAmount(escalation.amount)}
                </p>
              </div>
            )}
          </div>

          {/* Reason Badge */}
          {escalation.reason && (
            <div>
              <p className="text-xs text-muted-foreground uppercase mb-1">Reason</p>
              {getReasonBadge(escalation.reason)}
            </div>
          )}

          {/* Alert Box */}
          <div className="bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <Clock className="h-4 w-4 text-orange-600 dark:text-orange-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-orange-900 dark:text-orange-300">
                  Immediate Action Required
                </p>
                <p className="text-xs text-orange-700 dark:text-orange-400 mt-1">
                  This transaction requires your review and approval before processing can continue.
                </p>
              </div>
            </div>
          </div>

          {/* Auto-close countdown */}
          {countdown > 0 && (
            <div className="text-center">
              <p className="text-xs text-muted-foreground">
                Auto-closing in <span className="font-bold text-slate-900 dark:text-white">{countdown}s</span>
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="w-full sm:w-auto text-slate-900 dark:text-white"
          >
            Dismiss
          </Button>
          <Button
            onClick={handleViewDetails}
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white"
          >
            <AlertTriangle className="h-4 w-4 mr-2" />
            Review Now
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
