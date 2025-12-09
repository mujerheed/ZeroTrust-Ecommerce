"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { XCircle, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function OAuthErrorPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [error, setError] = useState<string>("");
    const [errorDetails, setErrorDetails] = useState<string>("");

    useEffect(() => {
        const errorParam = searchParams.get("error");
        const errorDescription = searchParams.get("error_description");

        if (errorParam) {
            setError(errorParam);
            setErrorDetails(errorDescription || "");
        } else {
            setError("Unknown error occurred during OAuth authentication");
        }
    }, [searchParams]);

    const getErrorMessage = () => {
        if (error.includes("access_denied")) {
            return "You denied access to your account. To use this integration, you need to grant the required permissions.";
        }
        if (error.includes("invalid_request")) {
            return "The OAuth request was invalid. Please try connecting again.";
        }
        if (error.includes("callback_failed")) {
            return "The OAuth callback failed. Please check your Meta app configuration.";
        }
        return errorDetails || "An unexpected error occurred during the connection process.";
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                        <XCircle className="h-10 w-10 text-red-600 dark:text-red-400" />
                    </div>
                    <CardTitle className="text-2xl">Connection Failed</CardTitle>
                    <CardDescription>
                        We couldn't connect your account
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                            {getErrorMessage()}
                        </AlertDescription>
                    </Alert>

                    {error && (
                        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                            <p className="text-xs text-muted-foreground font-mono break-all">
                                Error: {error}
                            </p>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Button
                            onClick={() => router.push("/ceo/integrations")}
                            className="w-full"
                        >
                            Try Again
                        </Button>
                        <Button
                            onClick={() => router.push("/ceo/dashboard")}
                            variant="outline"
                            className="w-full"
                        >
                            Back to Dashboard
                        </Button>
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                        <p className="text-xs text-blue-800 dark:text-blue-200">
                            <strong>Common issues:</strong>
                            <br />• Make sure you have a Facebook Business Page
                            <br />• Grant all requested permissions
                            <br />• Check your Meta app configuration
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
