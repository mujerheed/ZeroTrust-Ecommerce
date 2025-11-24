"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { toast } from "sonner";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  Settings as SettingsIcon, 
  ArrowLeft, 
  User, 
  Mail, 
  Phone, 
  Building2,
  Clock,
  Truck,
  CreditCard,
  Shield,
  MessageSquare,
  Save,
  Bell,
  Mail as MailIcon,
  Smartphone
} from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { CEOLayout } from "@/components/ceo/CEOLayout";

interface CEOProfile {
  user_id: string;
  name: string;
  email: string;
  phone: string;
  company_name?: string;
  business_hours?: string;
  delivery_fee?: number;
  bank_details?: {
    bank_name: string;
    account_number: string;
    account_name: string;
  };
  created_at: number;
}

interface ChatbotSettings {
  greeting_message?: string;
  greeting?: string;
  tone?: string;
  fallback_message?: string;
  business_hours?: string;
}

export default function SettingsPage() {
  const [profile, setProfile] = useState<CEOProfile | null>(null);
  const [chatbotSettings, setChatbotSettings] = useState<ChatbotSettings>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const router = useRouter();

  // Notification preferences state
  const [notificationPrefs, setNotificationPrefs] = useState({
    sms_high_value: true,
    email_daily_report: true,
    push_notifications: true,
    sms_flagged_orders: true,
    email_weekly_summary: false,
  });

  // Profile form state
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    company_name: "",
    business_hours: "",
    delivery_fee: "",
    bank_name: "",
    account_number: "",
    account_name: "",
  });

  // Chatbot form state
  const [chatbotData, setChatbotData] = useState({
    greeting_message: "",
    tone: "Professional",
    fallback_message: "",
    business_hours: "",
  });

  // OTP dialog state
  const [showOTPDialog, setShowOTPDialog] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);

  useEffect(() => {
    fetchProfile();
    fetchChatbotSettings();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get("/ceo/profile");
      const ceoData = response.data.data.ceo;
      setProfile(ceoData);

      // Populate form
      setFormData({
        name: ceoData.name || "",
        email: ceoData.email || "",
        phone: ceoData.phone || "",
        company_name: ceoData.company_name || "",
        business_hours: ceoData.business_hours || "",
        delivery_fee: ceoData.delivery_fee?.toString() || "",
        bank_name: ceoData.bank_details?.bank_name || "",
        account_number: ceoData.bank_details?.account_number || "",
        account_name: ceoData.bank_details?.account_name || "",
      });
    } catch (error: any) {
      console.error("Error fetching profile:", error);
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
        router.push("/ceo/login");
      } else {
        toast.error("Failed to load profile");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchChatbotSettings = async () => {
    try {
      const response = await api.get("/ceo/chatbot-settings");
      const settings = response.data.data || {};
      setChatbotSettings(settings);
      setChatbotData({
        greeting_message: settings.greeting_message || "",
        tone: settings.tone || "Professional",
        fallback_message: settings.fallback_message || "",
        business_hours: settings.business_hours || "",
      });
    } catch (error) {
      console.error("Error fetching chatbot settings:", error);
    }
  };

  const handleProfileUpdate = async () => {
    setSaving(true);
    try {
      const updateData: any = {
        company_name: formData.company_name,
        phone: formData.phone,
        business_hours: formData.business_hours,
        delivery_fee: formData.delivery_fee ? parseFloat(formData.delivery_fee) : null,
      };

      // Only include bank details if at least one field is filled
      if (formData.bank_name || formData.account_number || formData.account_name) {
        updateData.bank_details = {
          bank_name: formData.bank_name,
          account_number: formData.account_number,
          account_name: formData.account_name,
        };
      }

      const response = await api.patch("/ceo/profile", updateData);
      
      if (response.data.status === "success") {
        toast.success("Profile updated successfully!");
        fetchProfile(); // Refresh profile data
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleChatbotUpdate = async () => {
    setSaving(true);
    try {
      const response = await api.patch("/ceo/chatbot-settings", chatbotData);
      
      if (response.data.status === "success") {
        toast.success("Chatbot settings updated successfully!");
        fetchChatbotSettings(); // Refresh settings
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to update chatbot settings");
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationUpdate = async () => {
    setSaving(true);
    try {
      const response = await api.patch("/ceo/settings/notifications", {
        notification_preferences: notificationPrefs
      });
      
      if (response.data.status === "success") {
        toast.success("Notification preferences saved successfully!");
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to save notification preferences");
    } finally {
      setSaving(false);
    }
  };

  const requestEmailOTP = async () => {
    // This would need a separate endpoint to request OTP for email change
    toast.info("Email OTP feature coming soon");
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
            <SettingsIcon className="h-8 w-8 text-blue-600" />
            Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your profile, business details, and chatbot preferences
          </p>
        </div>

      {/* Tabs */}
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full max-w-3xl grid-cols-3">
          <TabsTrigger value="profile">Profile & Business</TabsTrigger>
          <TabsTrigger value="chatbot">Chatbot Settings</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Personal Information
              </CardTitle>
              <CardDescription>
                Your personal details and contact information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder={profile?.name || "Enter your full name"}
                    disabled
                  />
                  <p className="text-xs text-muted-foreground">
                    Name cannot be changed. Contact support if needed.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <div className="flex gap-2">
                    <Input
                      value={formData.email}
                      placeholder={profile?.email || "your@email.com"}
                      disabled
                    />
                    <Button variant="outline" size="sm" onClick={requestEmailOTP} disabled>
                      <Shield className="h-4 w-4 mr-2" />
                      Change
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Email change requires OTP verification
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder={profile?.phone || "+234 812 345 6789"}
                      className="pl-8"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Business Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                Business Information
              </CardTitle>
              <CardDescription>
                Your company details and operational hours
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Company Name</Label>
                  <Input
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    placeholder={profile?.company_name || "Your Company Ltd."}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Delivery Fee (₦)</Label>
                  <div className="relative">
                    <Truck className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      value={formData.delivery_fee}
                      onChange={(e) => setFormData({ ...formData, delivery_fee: e.target.value })}
                      placeholder={profile?.delivery_fee?.toString() || "2500"}
                      className="pl-8"
                    />
                  </div>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label>Business Hours</Label>
                  <div className="relative">
                    <Clock className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      value={formData.business_hours}
                      onChange={(e) => setFormData({ ...formData, business_hours: e.target.value })}
                      placeholder={profile?.business_hours || "Mon-Fri 9AM-6PM, Sat 10AM-4PM"}
                      className="pl-8"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bank Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Bank Account Details
              </CardTitle>
              <CardDescription>
                Account information for receiving payments
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Bank Name</Label>
                  <Input
                    value={formData.bank_name}
                    onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                    placeholder={profile?.bank_details?.bank_name || "Access Bank"}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Account Number</Label>
                  <Input
                    value={formData.account_number}
                    onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                    placeholder={profile?.bank_details?.account_number || "0123456789"}
                    maxLength={10}
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label>Account Name</Label>
                  <Input
                    value={formData.account_name}
                    onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                    placeholder={profile?.bank_details?.account_name || "Your Company Ltd."}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleProfileUpdate} disabled={saving} size="lg">
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Saving..." : "Save Profile Changes"}
            </Button>
          </div>
        </TabsContent>

        {/* Chatbot Settings Tab */}
        <TabsContent value="chatbot" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Chatbot Customization
              </CardTitle>
              <CardDescription>
                Customize how your automated chatbot interacts with buyers on WhatsApp/Instagram
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Greeting Message</Label>
                <Textarea
                  value={chatbotData.greeting_message}
                  onChange={(e) => setChatbotData({ ...chatbotData, greeting_message: e.target.value })}
                  placeholder={chatbotSettings?.greeting || "Welcome to [Company Name]! How can I help you today?"}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  First message buyers see when they start a conversation
                </p>
              </div>

              <div className="space-y-2">
                <Label>Tone of Voice</Label>
                <Select value={chatbotData.tone} onValueChange={(value) => setChatbotData({ ...chatbotData, tone: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Professional">Professional</SelectItem>
                    <SelectItem value="Friendly">Friendly</SelectItem>
                    <SelectItem value="Pidgin">Pidgin (Nigerian Pidgin English)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Choose the communication style for automated responses
                </p>
              </div>

              <div className="space-y-2">
                <Label>Fallback Message</Label>
                <Textarea
                  value={chatbotData.fallback_message}
                  onChange={(e) => setChatbotData({ ...chatbotData, fallback_message: e.target.value })}
                  placeholder={chatbotSettings?.fallback_message || "I don't understand that. Please contact our support team or rephrase your question."}
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  Message shown when the chatbot doesn't understand the buyer's query
                </p>
              </div>

              <div className="space-y-2">
                <Label>Business Hours (for chatbot)</Label>
                <Input
                  value={chatbotData.business_hours}
                  onChange={(e) => setChatbotData({ ...chatbotData, business_hours: e.target.value })}
                  placeholder={chatbotSettings?.business_hours || "Monday to Friday, 9AM - 6PM"}
                />
                <p className="text-xs text-muted-foreground">
                  Displayed to buyers when they message outside operating hours
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleChatbotUpdate} disabled={saving} size="lg">
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Saving..." : "Save Chatbot Settings"}
            </Button>
          </div>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notification Preferences
              </CardTitle>
              <CardDescription>
                Configure how you want to be notified about escalations and reports
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* SMS Notifications */}
              <div className="space-y-4">
                <h4 className="font-medium text-slate-900 dark:text-white flex items-center gap-2">
                  <Smartphone className="h-4 w-4" />
                  SMS Alerts
                </h4>
                
                <div className="flex items-center justify-between border-b pb-4">
                  <div className="space-y-0.5">
                    <Label className="text-base font-medium text-slate-900 dark:text-white">
                      High-Value Escalations
                    </Label>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Receive SMS when orders ≥ ₦1,000,000 require approval
                    </p>
                  </div>
                  <Switch
                    checked={notificationPrefs.sms_high_value}
                    onCheckedChange={(checked: boolean) =>
                      setNotificationPrefs({ ...notificationPrefs, sms_high_value: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between border-b pb-4">
                  <div className="space-y-0.5">
                    <Label className="text-base font-medium text-slate-900 dark:text-white">
                      Flagged Orders
                    </Label>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Receive SMS when vendors flag suspicious receipts
                    </p>
                  </div>
                  <Switch
                    checked={notificationPrefs.sms_flagged_orders}
                    onCheckedChange={(checked: boolean) =>
                      setNotificationPrefs({ ...notificationPrefs, sms_flagged_orders: checked })
                    }
                  />
                </div>
              </div>

              {/* Email Notifications */}
              <div className="space-y-4">
                <h4 className="font-medium text-slate-900 dark:text-white flex items-center gap-2">
                  <MailIcon className="h-4 w-4" />
                  Email Reports
                </h4>

                <div className="flex items-center justify-between border-b pb-4">
                  <div className="space-y-0.5">
                    <Label className="text-base font-medium text-slate-900 dark:text-white">
                      Daily Fraud Report
                    </Label>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Daily summary of flagged orders and suspicious activity
                    </p>
                  </div>
                  <Switch
                    checked={notificationPrefs.email_daily_report}
                    onCheckedChange={(checked: boolean) =>
                      setNotificationPrefs({ ...notificationPrefs, email_daily_report: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between border-b pb-4">
                  <div className="space-y-0.5">
                    <Label className="text-base font-medium text-slate-900 dark:text-white">
                      Weekly Summary
                    </Label>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Weekly analytics report with vendor performance metrics
                    </p>
                  </div>
                  <Switch
                    checked={notificationPrefs.email_weekly_summary}
                    onCheckedChange={(checked: boolean) =>
                      setNotificationPrefs({ ...notificationPrefs, email_weekly_summary: checked })
                    }
                  />
                </div>
              </div>

              {/* In-App Notifications */}
              <div className="space-y-4">
                <h4 className="font-medium text-slate-900 dark:text-white flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  In-App Notifications
                </h4>

                <div className="flex items-center justify-between border-b pb-4">
                  <div className="space-y-0.5">
                    <Label className="text-base font-medium text-slate-900 dark:text-white">
                      Push Notifications
                    </Label>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Real-time browser notifications for escalations (auto-pop modal)
                    </p>
                  </div>
                  <Switch
                    checked={notificationPrefs.push_notifications}
                    onCheckedChange={(checked: boolean) =>
                      setNotificationPrefs({ ...notificationPrefs, push_notifications: checked })
                    }
                  />
                </div>
              </div>

              {/* Info Alert */}
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex gap-3">
                  <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                      Security Notice
                    </p>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      High-value escalations (≥ ₦1,000,000) always require your approval regardless of notification settings.
                      This is a Zero Trust security requirement.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleNotificationUpdate} disabled={saving} size="lg">
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Saving..." : "Save Notification Preferences"}
            </Button>
          </div>
        </TabsContent>
      </Tabs>

      {/* OTP Dialog (for email changes - future feature) */}
      <Dialog open={showOTPDialog} onOpenChange={setShowOTPDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Verify Email Change</DialogTitle>
            <DialogDescription>
              Enter the OTP sent to your new email address
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex justify-center">
              <InputOTP maxLength={6} value={otp} onChange={setOtp}>
                <InputOTPGroup>
                  <InputOTPSlot index={0} />
                  <InputOTPSlot index={1} />
                  <InputOTPSlot index={2} />
                  <InputOTPSlot index={3} />
                  <InputOTPSlot index={4} />
                  <InputOTPSlot index={5} />
                </InputOTPGroup>
              </InputOTP>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowOTPDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => {}} disabled={otp.length !== 6}>
              Verify & Update Email
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </CEOLayout>
  );
}
