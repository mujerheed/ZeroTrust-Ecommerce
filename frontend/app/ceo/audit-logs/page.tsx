"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { toast } from "sonner";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  FileText, 
  Download, 
  Search, 
  Calendar,
  Shield,
  User,
  CheckCircle,
  XCircle,
  UserPlus,
  UserMinus,
  Package,
  AlertTriangle,
  FileCheck,
  ArrowLeft,
  Filter
} from "lucide-react";
import { CEOLayout } from "@/components/ceo/CEOLayout";

interface AuditLog {
  log_id: string;
  timestamp: number;
  ceo_id: string;
  user_id: string;
  action: string;
  details: Record<string, any>;
}

// Action type configurations
const ACTION_TYPES = [
  { value: "all", label: "All Actions" },
  { value: "order_approved", label: "Order Approved", icon: CheckCircle, color: "bg-green-500" },
  { value: "order_rejected", label: "Order Rejected", icon: XCircle, color: "bg-red-500" },
  { value: "vendor_created", label: "Vendor Created", icon: UserPlus, color: "bg-blue-500" },
  { value: "vendor_deleted", label: "Vendor Deleted", icon: UserMinus, color: "bg-orange-500" },
  { value: "vendor_updated", label: "Vendor Updated", icon: User, color: "bg-purple-500" },
  { value: "order_flagged", label: "Order Flagged", icon: AlertTriangle, color: "bg-yellow-500" },
  { value: "receipt_verified", label: "Receipt Verified", icon: FileCheck, color: "bg-teal-500" },
];

const getActionConfig = (action: string) => {
  return ACTION_TYPES.find(a => a.value === action) || { 
    value: action, 
    label: action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    icon: FileText,
    color: "bg-gray-500"
  };
};

// Mask phone numbers (show last 4 digits)
const maskPhone = (phone: string) => {
  if (!phone) return "N/A";
  if (phone.length <= 4) return phone;
  return "+234***" + phone.slice(-4);
};

// Mask user_id (show first 8 chars)
const maskUserId = (userId: string) => {
  if (!userId) return "N/A";
  if (userId.length <= 12) return userId.substring(0, 8) + "***";
  return userId.substring(0, 8) + "***";
};

// Format timestamp
const formatTimestamp = (timestamp: number) => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('en-NG', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
};

// Export to CSV
const exportToCSV = (logs: AuditLog[]) => {
  const headers = ["Timestamp", "Actor (Masked)", "Action", "Details"];
  const rows = logs.map(log => [
    formatTimestamp(log.timestamp),
    maskUserId(log.user_id),
    log.action,
    JSON.stringify(log.details).replace(/,/g, ';') // Replace commas in JSON
  ]);
  
  const csvContent = [
    headers.join(","),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
  ].join("\n");
  
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const router = useRouter();

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [logs, actionFilter, searchQuery, startDate, endDate]);

  const fetchAuditLogs = async () => {
    try {
      const response = await api.get("/ceo/audit-logs", {
        params: { limit: 500 }
      });

      const logs = response.data.data.logs || [];
      setLogs(logs);
      
      if (logs.length === 0) {
        toast.info("No audit logs found. Logs will appear as actions are performed.");
      }
    } catch (error: any) {
      console.error("Error fetching audit logs:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
        router.push("/ceo/login");
      } else {
        toast.error("Failed to load audit logs");
      }
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...logs];

    // Action type filter
    if (actionFilter !== "all") {
      filtered = filtered.filter(log => log.action === actionFilter);
    }

    // Search filter (search in action, user_id, details)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(log =>
        log.action.toLowerCase().includes(query) ||
        log.user_id.toLowerCase().includes(query) ||
        JSON.stringify(log.details).toLowerCase().includes(query)
      );
    }

    // Date range filter
    if (startDate) {
      const startTimestamp = new Date(startDate).getTime() / 1000;
      filtered = filtered.filter(log => log.timestamp >= startTimestamp);
    }

    if (endDate) {
      const endTimestamp = new Date(endDate + "T23:59:59").getTime() / 1000;
      filtered = filtered.filter(log => log.timestamp <= endTimestamp);
    }

    setFilteredLogs(filtered);
  };

  const clearFilters = () => {
    setActionFilter("all");
    setSearchQuery("");
    setStartDate("");
    setEndDate("");
  };

  return (
    <CEOLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Shield className="h-8 w-8 text-blue-600" />
              Audit Logs
            </h1>
            <p className="text-muted-foreground mt-1">
              Immutable security logs of all CEO and vendor actions
            </p>
          </div>
          <Button onClick={() => exportToCSV(filteredLogs)} disabled={filteredLogs.length === 0}>
            <Download className="h-4 w-4 mr-2" />
            Export to CSV
          </Button>
        </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Logs</CardDescription>
            <CardTitle className="text-3xl">{logs.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Filtered Results</CardDescription>
            <CardTitle className="text-3xl">{filteredLogs.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Latest Activity</CardDescription>
            <CardTitle className="text-sm">
              {logs.length > 0 ? formatTimestamp(logs[0]?.timestamp) : "No logs yet"}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filters Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                Filters
              </CardTitle>
              <CardDescription>
                Filter audit logs by action type, date range, or search keywords
              </CardDescription>
            </div>
            {(actionFilter !== "all" || searchQuery || startDate || endDate) && (
              <Button variant="ghost" onClick={clearFilters} size="sm">
                Clear All
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Action Type Filter */}
            <div className="space-y-2">
              <Label>Action Type</Label>
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ACTION_TYPES.map(type => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Search */}
            <div className="space-y-2">
              <Label>Search</Label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            {/* Start Date */}
            <div className="space-y-2">
              <Label>Start Date</Label>
              <div className="relative">
                <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            {/* End Date */}
            <div className="space-y-2">
              <Label>End Date</Label>
              <div className="relative">
                <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Audit Trail</CardTitle>
              <CardDescription>
                All actions are logged and cannot be modified or deleted
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-sm">
              {filteredLogs.length} {filteredLogs.length === 1 ? 'Entry' : 'Entries'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="text-muted-foreground">Loading audit logs...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <Shield className="h-12 w-12 mx-auto text-muted-foreground/50" />
              <div>
                <p className="text-lg font-medium">No audit logs found</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {logs.length === 0 
                    ? "Logs will appear here as actions are performed"
                    : "Try adjusting your filters to see more results"
                  }
                </p>
              </div>
              {(actionFilter !== "all" || searchQuery || startDate || endDate) && (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              )}
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[180px]">Timestamp</TableHead>
                      <TableHead className="w-[200px]">Action</TableHead>
                      <TableHead className="w-[150px]">Actor</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLogs.map((log) => {
                      const actionConfig = getActionConfig(log.action);
                      const ActionIcon = actionConfig.icon || FileText;
                      
                      return (
                        <TableRow key={log.log_id} className="hover:bg-muted/50">
                          <TableCell className="font-mono text-xs">
                            {formatTimestamp(log.timestamp)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="gap-1.5">
                              <ActionIcon className="h-3.5 w-3.5" />
                              {actionConfig.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-muted-foreground">
                            {maskUserId(log.user_id)}
                          </TableCell>
                          <TableCell>
                            <details className="cursor-pointer group">
                              <summary className="text-sm text-muted-foreground hover:text-foreground transition-colors list-none flex items-center gap-1">
                                <span className="group-open:rotate-90 transition-transform">▶</span>
                                View Details
                              </summary>
                              <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-auto max-h-40 border">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            </details>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
    </CEOLayout>
  );
}
