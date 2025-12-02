"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { toast } from "sonner";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ArrowLeft,
  Plug,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ExternalLink,
  Instagram as InstagramIcon,
  MessageCircle,
  Calendar,
  RefreshCw
} from "lucide-react";

import { CEOLayout } from "@/components/ceo/CEOLayout";

interface ConnectionStatus {
  platform: string;
  connected: boolean;
  connected_at?: number;
  expires_at?: number;
  days_until_expiry?: number;
  needs_refresh?: boolean;
  phone_number_id?: string;
  page_id?: string;
  business_account_id?: string;
}

export default function IntegrationsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [whatsappStatus, setWhatsappStatus] = useState<ConnectionStatus | null>(null);
  const [instagramStatus, setInstagramStatus] = useState<ConnectionStatus | null>(null);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);
  const [platformToDisconnect, setPlatformToDisconnect] = useState<string>("");

  useEffect(() => {
    fetchConnectionStatus();
  }, []);

  const fetchConnectionStatus = async () => {
    setLoading(true);
    try {
      // Fetch WhatsApp status
      const whatsappRes = await api.get("/ceo/oauth/meta/status?platform=whatsapp");
      setWhatsappStatus(whatsappRes.data.data);
    } catch (error: any) {
      if (error.response?.status !== 404) {
        console.error("Failed to fetch WhatsApp status:", error);
      }
      setWhatsappStatus({ platform: "whatsapp", connected: false });
    }

    try {
      // Fetch Instagram status
      const instagramRes = await api.get("/ceo/oauth/meta/status?platform=instagram");
      setInstagramStatus(instagramRes.data.data);
    } catch (error: any) {
      if (error.response?.status !== 404) {
        console.error("Failed to fetch Instagram status:", error);
      }
      setInstagramStatus({ platform: "instagram", connected: false });
    }

    setLoading(false);
  };

  const handleConnect = async (platform: string) => {
    try {
      // Create a temporary OAuth session
      // This generates a short-lived, single-use token that's safe to use in URLs
      const response = await api.post(`/ceo/oauth/meta/create-session?platform=${platform}`);

      const { auth_url } = response.data.data;

      // Redirect to the authorization URL
      // The URL contains a temporary session token instead of the JWT
      window.location.href = auth_url;
    } catch (error: any) {
      toast.error(error.response?.data?.detail || `Failed to connect ${platform}`);
      console.error(error);
    }
  };

  const confirmDisconnect = (platform: string) => {
    setPlatformToDisconnect(platform);
    setShowDisconnectDialog(true);
  };

  const handleDisconnect = async () => {
    if (!platformToDisconnect) return;

    setDisconnecting(platformToDisconnect);
    setShowDisconnectDialog(false);

    try {
      await api.post(`/ceo/oauth/meta/revoke?platform=${platformToDisconnect}`);
      toast.success(`${platformToDisconnect === "whatsapp" ? "WhatsApp" : "Instagram"} disconnected successfully`);

      // Refresh status
      await fetchConnectionStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.message || `Failed to disconnect ${platformToDisconnect}`);
    } finally {
      setDisconnecting(null);
      setPlatformToDisconnect("");
    }
  };

  const formatDate = (timestamp?: number) => {
    if (!timestamp) return "N/A";
    return new Date(timestamp * 1000).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const renderConnectionCard = (
    title: string,
    description: string,
    status: ConnectionStatus | null,
    icon: React.ReactNode,
    platform: string
  ) => {
    const isConnected = status?.connected || false;
    const needsRefresh = status?.needs_refresh || false;

    return (
      <Card className={isConnected ? "border-green-200 bg-green-50/50" : ""}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${isConnected ? "bg-green-100" : "bg-gray-100"}`}>
                {icon}
              </div>
              <div>
                <CardTitle className="flex items-center gap-2">
                  {title}
                  {isConnected && (
                    <Badge variant="default" className="bg-green-600">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Connected
                    </Badge>
                  )}
                  {!isConnected && (
                    <Badge variant="secondary">
                      <XCircle className="h-3 w-3 mr-1" />
                      Not Connected
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="mt-1">{description}</CardDescription>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {isConnected && (
            <>
              {/* Connection Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Connected Since</p>
                  <p className="font-medium flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(status?.connected_at)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Token Expires</p>
                  <p className="font-medium flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(status?.expires_at)}
                  </p>
                </div>
                {status?.days_until_expiry !== undefined && (
                  <div className="md:col-span-2">
                    <p className="text-muted-foreground">Days Until Expiry</p>
                    <p className="font-medium text-lg">
                      {status.days_until_expiry} days
                    </p>
                  </div>
                )}
                {status?.phone_number_id && (
                  <div>
                    <p className="text-muted-foreground">Phone Number ID</p>
                    <p className="font-mono text-xs">{status.phone_number_id}</p>
                  </div>
                )}
                {status?.page_id && (
                  <div>
                    <p className="text-muted-foreground">Page ID</p>
                    <p className="font-mono text-xs">{status.page_id}</p>
                  </div>
                )}
              </div>

              {/* Expiry Warning */}
              {needsRefresh && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Token expires in less than 7 days. Please reconnect to refresh your access token.
                  </AlertDescription>
                </Alert>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                {needsRefresh && (
                  <Button
                    onClick={() => handleConnect(platform)}
                    variant="default"
                    size="sm"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh Connection
                  </Button>
                )}
                <Button
                  onClick={() => confirmDisconnect(platform)}
                  variant="destructive"
                  size="sm"
                  disabled={disconnecting === platform}
                >
                  {disconnecting === platform ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Disconnecting...
                    </>
                  ) : (
                    "Disconnect"
                  )}
                </Button>
              </div>
            </>
          )}

          {!isConnected && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Connect your {title} account to enable automated chatbot responses and buyer authentication.
              </p>
              <Button
                onClick={() => handleConnect(platform)}
                className="w-full"
                size="lg"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Connect {title}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <CEOLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </CEOLayout>
    );
  }

  return (
    <CEOLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Plug className="h-8 w-8 text-blue-600" />
            Integrations
          </h1>
          <p className="text-muted-foreground mt-1">
            Connect your WhatsApp Business and Instagram accounts for automated messaging
          </p>
        </div>

        {/* Info Alert */}
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Multi-Tenancy Support:</strong> Each CEO business operates independently. Your OAuth tokens are securely stored and isolated from other businesses. Connections enable automated buyer authentication and order notifications via WhatsApp/Instagram DMs.
          </AlertDescription>
        </Alert>

        {/* Connection Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* WhatsApp Business */}
          {renderConnectionCard(
            "WhatsApp Business",
            "Enable buyer OTP delivery and automated order notifications via WhatsApp",
            whatsappStatus,
            <MessageCircle className="h-6 w-6 text-green-600" />,
            "whatsapp"
          )}

          {/* Instagram Business */}
          {renderConnectionCard(
            "Instagram Business",
            "Enable buyer discovery and authentication via Instagram DMs",
            instagramStatus,
            <InstagramIcon className="h-6 w-6 text-pink-600" />,
            "instagram"
          )}
        </div>

        {/* OAuth Information */}
        <Card>
          <CardHeader>
            <CardTitle>About OAuth Connections</CardTitle>
            <CardDescription>
              How Meta OAuth integration works with TrustGuard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <h4 className="font-semibold mb-1">🔒 Security</h4>
              <p className="text-muted-foreground">
                OAuth tokens are encrypted and stored in AWS Secrets Manager. Each CEO's tokens are isolated and never shared with other businesses.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">⏱️ Token Expiry</h4>
              <p className="text-muted-foreground">
                Meta access tokens expire after 60 days. You'll be notified when tokens need refresh (less than 7 days remaining). Simply reconnect to refresh.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">📱 Required Permissions</h4>
              <p className="text-muted-foreground">
                <strong>WhatsApp:</strong> Business management, messaging, account management<br />
                <strong>Instagram:</strong> Basic profile, manage messages, pages messaging
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">🔌 Disconnecting</h4>
              <p className="text-muted-foreground">
                Disconnecting removes stored tokens and disables automated messaging. Your order and buyer data remains intact.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Disconnect Confirmation Dialog */}
        <Dialog open={showDisconnectDialog} onOpenChange={setShowDisconnectDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Disconnect {platformToDisconnect === "whatsapp" ? "WhatsApp" : "Instagram"}?</DialogTitle>
              <DialogDescription>
                This will remove your OAuth connection and disable automated messaging on {platformToDisconnect === "whatsapp" ? "WhatsApp" : "Instagram"}.
                Your order history and buyer data will not be affected.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDisconnectDialog(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDisconnect}>
                Disconnect
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </CEOLayout>
  );
}
