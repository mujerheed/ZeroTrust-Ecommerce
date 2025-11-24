"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { CEOLayout } from "@/components/ceo/CEOLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from "recharts";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  ShieldCheck,
  Download,
  Users,
  Clock,
  Flag,
  CheckCircle,
  XCircle,
} from "lucide-react";

interface VendorPerformance {
  vendor_id: string;
  vendor_name: string;
  total_orders: number;
  flagged_orders: number;
  approved_orders: number;
  rejected_orders: number;
  flag_rate: number;
  avg_approval_time_hours: number;
  total_revenue: number;
}

interface FraudInsight {
  flagged_reason: string;
  count: number;
  percentage: number;
}

interface AnalyticsData {
  vendor_performance: VendorPerformance[];
  fraud_insights: FraudInsight[];
  summary: {
    total_vendors: number;
    total_orders: number;
    total_flagged: number;
    total_approved: number;
    total_rejected: number;
    overall_flag_rate: number;
    avg_approval_time_hours: number;
  };
  trend_data?: {
    date: string;
    flagged_count: number;
    approved_count: number;
  }[];
}

const COLORS = ["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e", "#14b8a6", "#06b6d4", "#3b82f6"];

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchAnalytics();
  }, []);

  async function fetchAnalytics() {
    try {
      setLoading(true);
      const response = await api.get("/ceo/analytics");
      
      // Mock data for development (replace with actual API response)
      const mockData: AnalyticsData = {
        vendor_performance: [
          {
            vendor_id: "v1",
            vendor_name: "Bisi Ojo",
            total_orders: 45,
            flagged_orders: 3,
            approved_orders: 40,
            rejected_orders: 2,
            flag_rate: 6.67,
            avg_approval_time_hours: 2.5,
            total_revenue: 1250000,
          },
          {
            vendor_id: "v2",
            vendor_name: "Chidi Okonkwo",
            total_orders: 38,
            flagged_orders: 8,
            approved_orders: 28,
            rejected_orders: 2,
            flag_rate: 21.05,
            avg_approval_time_hours: 4.2,
            total_revenue: 980000,
          },
          {
            vendor_id: "v3",
            vendor_name: "Amina Yusuf",
            total_orders: 52,
            flagged_orders: 2,
            approved_orders: 49,
            rejected_orders: 1,
            flag_rate: 3.85,
            avg_approval_time_hours: 1.8,
            total_revenue: 1560000,
          },
          {
            vendor_id: "v4",
            vendor_name: "Tunde Adebayo",
            total_orders: 29,
            flagged_orders: 5,
            approved_orders: 22,
            rejected_orders: 2,
            flag_rate: 17.24,
            avg_approval_time_hours: 3.1,
            total_revenue: 720000,
          },
        ],
        fraud_insights: [
          { flagged_reason: "Receipt mismatch", count: 8, percentage: 44.4 },
          { flagged_reason: "High-value transaction", count: 5, percentage: 27.8 },
          { flagged_reason: "Suspicious pattern", count: 3, percentage: 16.7 },
          { flagged_reason: "Duplicate receipt", count: 2, percentage: 11.1 },
        ],
        summary: {
          total_vendors: 4,
          total_orders: 164,
          total_flagged: 18,
          total_approved: 139,
          total_rejected: 7,
          overall_flag_rate: 10.98,
          avg_approval_time_hours: 2.9,
        },
        trend_data: [
          { date: "Week 1", flagged_count: 3, approved_count: 28 },
          { date: "Week 2", flagged_count: 5, approved_count: 32 },
          { date: "Week 3", flagged_count: 4, approved_count: 35 },
          { date: "Week 4", flagged_count: 6, approved_count: 44 },
        ],
      };

      setData(mockData);
    } catch (error: any) {
      console.error("Analytics fetch error:", error);
      toast.error("Failed to load analytics data");
      
      if (error.response?.status === 401) {
        router.push("/ceo/login");
      }
    } finally {
      setLoading(false);
    }
  }

  function exportToPDF() {
    if (!data) return;

    // Create a printable HTML content
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error("Please allow popups to export PDF");
      return;
    }

    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Vendor Analytics Report - ${new Date().toLocaleDateString()}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
          }
          h1 {
            color: #1e293b;
            margin-bottom: 10px;
          }
          .summary {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
          }
          .summary-card {
            border: 1px solid #e2e8f0;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            border-radius: 4px;
          }
          .summary-card h3 {
            margin: 0;
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
          }
          .summary-card p {
            margin: 5px 0 0 0;
            font-size: 24px;
            font-weight: bold;
            color: #1e293b;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
          }
          th, td {
            border: 1px solid #e2e8f0;
            padding: 12px;
            text-align: left;
          }
          th {
            background-color: #f1f5f9;
            font-weight: 600;
            color: #1e293b;
          }
          .flag-rate-excellent { color: #22c55e; font-weight: 600; }
          .flag-rate-good { color: #eab308; font-weight: 600; }
          .flag-rate-review { color: #ef4444; font-weight: 600; }
          .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #64748b;
            font-size: 12px;
          }
          @media print {
            body { padding: 0; }
            .no-print { display: none; }
          }
        </style>
      </head>
      <body>
        <h1>📊 Vendor Analytics Report</h1>
        <p style="color: #64748b; margin: 0 0 20px 0;">Generated on ${new Date().toLocaleString()}</p>
        
        <div class="summary">
          <div class="summary-card">
            <h3>Total Vendors</h3>
            <p>${data.summary.total_vendors}</p>
          </div>
          <div class="summary-card">
            <h3>Total Orders</h3>
            <p>${data.summary.total_orders}</p>
          </div>
          <div class="summary-card">
            <h3>Flagged Orders</h3>
            <p>${data.summary.total_flagged}</p>
          </div>
          <div class="summary-card">
            <h3>Avg Approval Time</h3>
            <p>${data.summary.avg_approval_time_hours.toFixed(1)}h</p>
          </div>
        </div>

        <h2 style="margin-top: 30px; color: #1e293b;">Vendor Performance</h2>
        <table>
          <thead>
            <tr>
              <th>Vendor Name</th>
              <th>Total Orders</th>
              <th>Flagged</th>
              <th>Approved</th>
              <th>Rejected</th>
              <th>Flag Rate</th>
              <th>Avg Time (hrs)</th>
              <th>Revenue (₦)</th>
            </tr>
          </thead>
          <tbody>
            ${data.vendor_performance.map(v => {
              const flagClass = v.flag_rate < 5 ? 'flag-rate-excellent' : v.flag_rate < 15 ? 'flag-rate-good' : 'flag-rate-review';
              return `
                <tr>
                  <td><strong>${v.vendor_name}</strong></td>
                  <td>${v.total_orders}</td>
                  <td>${v.flagged_orders}</td>
                  <td>${v.approved_orders}</td>
                  <td>${v.rejected_orders}</td>
                  <td class="${flagClass}">${v.flag_rate.toFixed(2)}%</td>
                  <td>${v.avg_approval_time_hours.toFixed(1)}</td>
                  <td>₦${v.total_revenue.toLocaleString()}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>

        <h2 style="margin-top: 30px; color: #1e293b;">Top Flagged Reasons</h2>
        <table>
          <thead>
            <tr>
              <th>Reason</th>
              <th>Count</th>
              <th>Percentage</th>
            </tr>
          </thead>
          <tbody>
            ${data.fraud_insights.map(f => `
              <tr>
                <td>${f.flagged_reason}</td>
                <td>${f.count}</td>
                <td>${f.percentage.toFixed(1)}%</td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div class="footer">
          <p><strong>TrustGuard Analytics</strong> | Zero Trust Security for E-Commerce</p>
          <p>This report contains confidential business information</p>
        </div>

        <div class="no-print" style="margin-top: 20px; text-align: center;">
          <button onclick="window.print()" style="background: #3b82f6; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
            🖨️ Print / Save as PDF
          </button>
          <button onclick="window.close()" style="background: #64748b; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-left: 10px;">
            ✕ Close
          </button>
        </div>
      </body>
      </html>
    `;

    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    // Auto-print after content loads
    printWindow.onload = () => {
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
      }, 250);
    };

    toast.success("PDF preview opened - use Print to save as PDF");
  }

  function exportToCSV() {
    if (!data) return;

    const csvRows = [
      ["Vendor Name", "Total Orders", "Flagged", "Approved", "Rejected", "Flag Rate %", "Avg Approval Time (hrs)", "Total Revenue (₦)"],
      ...data.vendor_performance.map((v) => [
        v.vendor_name,
        v.total_orders,
        v.flagged_orders,
        v.approved_orders,
        v.rejected_orders,
        v.flag_rate.toFixed(2),
        v.avg_approval_time_hours.toFixed(1),
        v.total_revenue.toLocaleString(),
      ]),
    ];

    const csvContent = csvRows.map((row) => row.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `vendor_analytics_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success("CSV exported successfully");
  }

  if (loading) {
    return (
      <CEOLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-muted-foreground">Loading analytics...</p>
          </div>
        </div>
      </CEOLayout>
    );
  }

  if (!data) {
    return (
      <CEOLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <p className="text-muted-foreground">No analytics data available</p>
        </div>
      </CEOLayout>
    );
  }

  return (
    <CEOLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="h-9 w-9 text-blue-600" />
              Analytics & Insights
            </h1>
            <p className="text-muted-foreground mt-1">
              Vendor performance metrics and fraud detection insights
            </p>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={exportToCSV}
              className="text-slate-900 dark:text-white border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button 
              onClick={exportToPDF}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Vendors</CardTitle>
              <Users className="h-5 w-5 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{data.summary.total_vendors}</div>
              <p className="text-xs text-muted-foreground mt-1">Active in system</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Approved Orders</CardTitle>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{data.summary.total_approved}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {((data.summary.total_approved / data.summary.total_orders) * 100).toFixed(1)}% of total
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Flagged Orders</CardTitle>
              <Flag className="h-5 w-5 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">{data.summary.total_flagged}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {data.summary.overall_flag_rate.toFixed(1)}% flag rate
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-purple-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Approval Time</CardTitle>
              <Clock className="h-5 w-5 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">
                {data.summary.avg_approval_time_hours.toFixed(1)}h
              </div>
              <p className="text-xs text-muted-foreground mt-1">CEO review time</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Fraud Insights Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                Fraud Insights Breakdown
              </CardTitle>
              <CardDescription>Top reasons for flagged receipts</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.fraud_insights.map((item) => ({
                      name: item.flagged_reason,
                      value: item.count,
                    }))}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {data.fraud_insights.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" />
                Weekly Trend Analysis
              </CardTitle>
              <CardDescription>Flagged vs Approved orders over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.trend_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="flagged_count" stroke="#f97316" name="Flagged" strokeWidth={2} />
                  <Line type="monotone" dataKey="approved_count" stroke="#22c55e" name="Approved" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Vendor Performance Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-blue-600" />
              Vendor Performance Table
            </CardTitle>
            <CardDescription>
              Detailed performance metrics for all {data.vendor_performance.length} vendors
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor Name</TableHead>
                    <TableHead className="text-center">Total Orders</TableHead>
                    <TableHead className="text-center">Flagged</TableHead>
                    <TableHead className="text-center">Approved</TableHead>
                    <TableHead className="text-center">Rejected</TableHead>
                    <TableHead className="text-center">Flag Rate</TableHead>
                    <TableHead className="text-center">Avg Approval Time</TableHead>
                    <TableHead className="text-right">Total Revenue</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.vendor_performance.map((vendor) => {
                    const flagRateLevel =
                      vendor.flag_rate < 5 ? "excellent" : vendor.flag_rate < 15 ? "good" : "warning";

                    return (
                      <TableRow key={vendor.vendor_id}>
                        <TableCell className="font-medium">{vendor.vendor_name}</TableCell>
                        <TableCell className="text-center">{vendor.total_orders}</TableCell>
                        <TableCell className="text-center">
                          <span className="text-orange-600 font-semibold">{vendor.flagged_orders}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="text-green-600 font-semibold">{vendor.approved_orders}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <span className="text-red-600 font-semibold">{vendor.rejected_orders}</span>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge
                            variant={flagRateLevel === "excellent" ? "default" : "destructive"}
                            className={
                              flagRateLevel === "excellent"
                                ? "bg-green-500"
                                : flagRateLevel === "good"
                                ? "bg-yellow-500"
                                : "bg-red-500"
                            }
                          >
                            {vendor.flag_rate.toFixed(1)}%
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center text-sm text-muted-foreground">
                          {vendor.avg_approval_time_hours.toFixed(1)}h
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          ₦{vendor.total_revenue.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-center">
                          {flagRateLevel === "excellent" ? (
                            <Badge variant="outline" className="gap-1 text-green-600 border-green-600">
                              <CheckCircle className="h-3 w-3" /> Excellent
                            </Badge>
                          ) : flagRateLevel === "good" ? (
                            <Badge variant="outline" className="gap-1 text-yellow-600 border-yellow-600">
                              <ShieldCheck className="h-3 w-3" /> Good
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="gap-1 text-red-600 border-red-600">
                              <AlertTriangle className="h-3 w-3" /> Review
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Fraud Insights List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Flag className="h-5 w-5 text-red-600" />
              Top Flagged Reasons
            </CardTitle>
            <CardDescription>Most common issues detected by the system</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.fraud_insights.map((insight, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg border bg-slate-50 dark:bg-slate-900">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{insight.flagged_reason}</p>
                      <p className="text-sm text-muted-foreground">{insight.count} incidents</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-base font-semibold">
                    {insight.percentage.toFixed(1)}%
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </CEOLayout>
  );
}
