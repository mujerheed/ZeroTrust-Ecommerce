"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function OAuthSuccessPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [platform, setPlatform] = useState<string>("");

    useEffect(() => {
        const platformParam = searchParams.get("platform");
        if (platformParam) {
            setPlatform(platformParam === "whatsapp" ? "WhatsApp Business" : "Instagram");
        }
    }, [searchParams]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                        <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
                    </div>
                    <CardTitle className="text-2xl">Connection Successful!</CardTitle>
                    <CardDescription>
                        {platform ? `Your ${platform} account has been connected successfully.` : "Your account has been connected successfully."}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                        <p className="text-sm text-green-800 dark:text-green-200">
                            ✅ OAuth authentication completed
                            <br />
                            ✅ Access token stored securely
                            <br />
                            ✅ Integration is now active
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Button
                            onClick={() => router.push("/ceo/integrations")}
                            className="w-full"
                        >
                            Go to Integrations
                        </Button>
                        <Button
                            onClick={() => router.push("/ceo/dashboard")}
                            variant="outline"
                            className="w-full"
                        >
                            Back to Dashboard
                        </Button>
                    </div>

                    {platform && (
                        <p className="text-xs text-center text-muted-foreground">
                            You can now receive messages from customers via {platform}
                        </p>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
