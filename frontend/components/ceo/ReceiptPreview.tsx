"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Download, ZoomIn, ZoomOut, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import Image from "next/image";

interface ReceiptData {
  has_receipt: boolean;
  receipt_id?: string;
  image_url?: string;
  url_expires_in?: number;
  receipt_metadata?: {
    uploaded_at: string;
    status: string;
    file_type: string;
    file_size: number;
  };
  ocr_data?: {
    available: boolean;
    extracted_text: string;
    confidence_score: number;
    amount?: number;
    account_number?: string;
  };
  mismatch_warnings?: Array<{
    type: string;
    severity: string;
    message: string;
    expected?: any;
    actual?: any;
    difference?: number;
  }>;
  order_details?: {
    order_id: string;
    expected_amount: number;
    vendor_id: string;
    buyer_id: string;
  };
}

interface ReceiptPreviewProps {
  orderId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ReceiptPreview({ orderId, isOpen, onClose }: ReceiptPreviewProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<ReceiptData | null>(null);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (isOpen && orderId) {
      fetchReceipt();
    }
  }, [isOpen, orderId]);

  const fetchReceipt = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("ceo_token");
      if (!token) {
        throw new Error("Authentication required");
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/ceo/orders/${orderId}/receipt`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to fetch receipt");
      }

      const result = await response.json();
      setReceipt(result.data);
    } catch (err: any) {
      setError(err.message || "Failed to load receipt");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!receipt?.image_url) return;

    try {
      const response = await fetch(receipt.image_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `receipt_${orderId}.${receipt.receipt_metadata?.file_type || "png"}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
    }).format(amount);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "border-red-600 bg-red-50 dark:bg-red-950";
      case "high":
        return "border-orange-600 bg-orange-50 dark:bg-orange-950";
      case "medium":
        return "border-yellow-600 bg-yellow-50 dark:bg-yellow-950";
      default:
        return "border-blue-600 bg-blue-50 dark:bg-blue-950";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-slate-900 dark:text-white">Receipt Preview</DialogTitle>
          <DialogDescription className="text-slate-600 dark:text-slate-400">
            Order ID: {orderId}
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-slate-600 dark:text-slate-400">Loading receipt...</span>
          </div>
        )}

        {error && (
          <Alert className="border-red-600 bg-red-50 dark:bg-red-950">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertTitle className="text-red-900 dark:text-red-200">Error</AlertTitle>
            <AlertDescription className="text-red-700 dark:text-red-300">{error}</AlertDescription>
          </Alert>
        )}

        {!loading && !error && receipt && !receipt.has_receipt && (
          <Alert className="border-blue-600 bg-blue-50 dark:bg-blue-950">
            <AlertTriangle className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-900 dark:text-blue-200">No Receipt</AlertTitle>
            <AlertDescription className="text-blue-700 dark:text-blue-300">
              No receipt has been uploaded for this order yet.
            </AlertDescription>
          </Alert>
        )}

        {!loading && !error && receipt && receipt.has_receipt && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Receipt Image */}
            <div className="lg:col-span-2 space-y-4">
              {/* Mismatch Warnings */}
              {receipt.mismatch_warnings && receipt.mismatch_warnings.length > 0 && (
                <div className="space-y-2">
                  {receipt.mismatch_warnings.map((warning, idx) => (
                    <Alert key={idx} className={getSeverityColor(warning.severity)}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertTitle className="font-semibold">
                        {warning.severity.toUpperCase()} - {warning.type.replace("_", " ").toUpperCase()}
                      </AlertTitle>
                      <AlertDescription>{warning.message}</AlertDescription>
                      {warning.difference && (
                        <AlertDescription className="mt-1 text-sm">
                          Difference: {formatCurrency(warning.difference)}
                        </AlertDescription>
                      )}
                    </Alert>
                  ))}
                </div>
              )}

              {/* Image Display */}
              <div className="border rounded-lg overflow-hidden bg-slate-100 dark:bg-slate-800">
                {receipt.image_url ? (
                  <div className="relative">
                    <div className="flex items-center justify-between p-3 border-b bg-white dark:bg-slate-900">
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setZoom(Math.max(50, zoom - 10))}
                          disabled={zoom <= 50}
                        >
                          <ZoomOut className="h-4 w-4" />
                        </Button>
                        <span className="text-sm text-slate-600 dark:text-slate-400 min-w-[60px] text-center">
                          {zoom}%
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setZoom(Math.min(200, zoom + 10))}
                          disabled={zoom >= 200}
                        >
                          <ZoomIn className="h-4 w-4" />
                        </Button>
                      </div>
                      <Button size="sm" onClick={handleDownload}>
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </div>
                    <div className="p-4 overflow-auto max-h-[600px]">
                      <img
                        src={receipt.image_url}
                        alt="Receipt"
                        style={{ width: `${zoom}%` }}
                        className="mx-auto"
                      />
                    </div>
                    <div className="p-2 bg-yellow-50 dark:bg-yellow-950 border-t text-xs text-yellow-800 dark:text-yellow-200 text-center">
                      ⏱️ This URL expires in {Math.floor((receipt.url_expires_in || 300) / 60)} minutes
                    </div>
                  </div>
                ) : (
                  <div className="p-12 text-center text-slate-500 dark:text-slate-400">
                    Receipt image unavailable
                  </div>
                )}
              </div>
            </div>

            {/* Receipt Metadata & OCR Data */}
            <div className="space-y-4">
              {/* Metadata */}
              <div className="border rounded-lg p-4 bg-white dark:bg-slate-900">
                <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Receipt Details</h3>
                {receipt.receipt_metadata && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">Status:</span>
                      <span className="ml-2 font-medium text-slate-900 dark:text-white">
                        {receipt.receipt_metadata.status}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">Uploaded:</span>
                      <span className="ml-2 font-medium text-slate-900 dark:text-white">
                        {new Date(receipt.receipt_metadata.uploaded_at).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">File Type:</span>
                      <span className="ml-2 font-medium text-slate-900 dark:text-white uppercase">
                        {receipt.receipt_metadata.file_type}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">File Size:</span>
                      <span className="ml-2 font-medium text-slate-900 dark:text-white">
                        {formatFileSize(receipt.receipt_metadata.file_size)}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* OCR Data */}
              {receipt.ocr_data?.available && (
                <div className="border rounded-lg p-4 bg-white dark:bg-slate-900">
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    OCR Analysis
                  </h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">Confidence:</span>
                      <span className="ml-2 font-medium text-slate-900 dark:text-white">
                        {(receipt.ocr_data.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    {receipt.ocr_data.amount && (
                      <div>
                        <span className="text-slate-600 dark:text-slate-400">Extracted Amount:</span>
                        <span className="ml-2 font-medium text-slate-900 dark:text-white">
                          {formatCurrency(receipt.ocr_data.amount)}
                        </span>
                      </div>
                    )}
                    {receipt.ocr_data.account_number && (
                      <div>
                        <span className="text-slate-600 dark:text-slate-400">Account Number:</span>
                        <span className="ml-2 font-mono text-slate-900 dark:text-white">
                          {receipt.ocr_data.account_number}
                        </span>
                      </div>
                    )}
                    {receipt.ocr_data.extracted_text && (
                      <div>
                        <span className="text-slate-600 dark:text-slate-400 block mb-2">Extracted Text:</span>
                        <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded text-xs max-h-32 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-slate-700 dark:text-slate-300">
                            {receipt.ocr_data.extracted_text}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Order Details */}
              {receipt.order_details && (
                <div className="border rounded-lg p-4 bg-white dark:bg-slate-900">
                  <h3 className="font-semibold text-slate-900 dark:text-white mb-3">Order Information</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">Expected Amount:</span>
                      <span className="ml-2 font-medium text-slate-900 dark:text-white">
                        {formatCurrency(receipt.order_details.expected_amount)}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">Vendor ID:</span>
                      <span className="ml-2 font-mono text-xs text-slate-900 dark:text-white">
                        {receipt.order_details.vendor_id}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600 dark:text-slate-400">Buyer ID:</span>
                      <span className="ml-2 font-mono text-xs text-slate-900 dark:text-white">
                        {receipt.order_details.buyer_id}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
