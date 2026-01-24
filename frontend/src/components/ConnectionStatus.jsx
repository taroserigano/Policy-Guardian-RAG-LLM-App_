/**
 * Connection status indicator component.
 * Shows when the API is unreachable and provides retry functionality.
 */
import { useState, useEffect, useCallback } from "react";
import { WifiOff, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { API_BASE_URL } from "../api/client";

export default function ConnectionStatus() {
  const [isOnline, setIsOnline] = useState(true);
  const [isApiReachable, setIsApiReachable] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [showBanner, setShowBanner] = useState(false);

  const checkApiHealth = useCallback(async () => {
    try {
      setIsChecking(true);
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });
      setIsApiReachable(response.ok);
      return response.ok;
    } catch (error) {
      setIsApiReachable(false);
      return false;
    } finally {
      setIsChecking(false);
    }
  }, []);

  // Check online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Check API health periodically when offline
  useEffect(() => {
    // Initial check
    checkApiHealth();

    // Only check frequently if we're disconnected
    const interval = setInterval(() => {
      if (!isOnline || !isApiReachable) {
        checkApiHealth();
      }
    }, 10000); // Check every 10 seconds when disconnected

    return () => clearInterval(interval);
  }, [isOnline, isApiReachable, checkApiHealth]);

  // Show/hide banner based on connection status
  useEffect(() => {
    if (!isOnline || !isApiReachable) {
      setShowBanner(true);
    } else {
      // Delay hiding to show success animation
      const timer = setTimeout(() => setShowBanner(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [isOnline, isApiReachable]);

  const handleRetry = () => {
    checkApiHealth();
  };

  if (!showBanner) return null;

  const isConnected = isOnline && isApiReachable;

  return (
    <div
      className={`fixed bottom-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
        showBanner ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
      }`}
    >
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg backdrop-blur-md border ${
          isConnected
            ? "bg-emerald-500/15 border-emerald-500/30"
            : "bg-red-500/15 border-red-500/30"
        }`}
      >
        {isConnected ? (
          <>
            <CheckCircle className="h-5 w-5 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-400">
              Connected
            </span>
          </>
        ) : (
          <>
            {!isOnline ? (
              <>
                <WifiOff className="h-5 w-5 text-red-400" />
                <span className="text-sm font-medium text-red-400">
                  No internet connection
                </span>
              </>
            ) : (
              <>
                <AlertCircle className="h-5 w-5 text-red-400" />
                <span className="text-sm font-medium text-red-400">
                  Server unreachable
                </span>
              </>
            )}
            <button
              onClick={handleRetry}
              disabled={isChecking}
              className="ml-2 p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={`h-4 w-4 ${isChecking ? "animate-spin" : ""}`}
              />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
