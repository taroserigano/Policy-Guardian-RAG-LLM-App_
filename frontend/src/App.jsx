/**
 * Main App component with routing.
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider } from "./contexts/AuthContext";
import ErrorBoundary from "./components/ErrorBoundary";
import ConnectionStatus from "./components/ConnectionStatus";
import KeyboardShortcuts from "./components/KeyboardShortcuts";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";
import CompliancePage from "./pages/CompliancePage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <ErrorBoundary>
            <BrowserRouter>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Protected routes */}
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Routes>
                          <Route
                            path="/"
                            element={<Navigate to="/upload" replace />}
                          />
                          <Route path="/upload" element={<UploadPage />} />
                          <Route path="/chat" element={<ChatPage />} />
                          <Route
                            path="/compliance"
                            element={<CompliancePage />}
                          />
                        </Routes>
                      </Layout>
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </BrowserRouter>
          </ErrorBoundary>
          {/* Connection status indicator */}
          <ConnectionStatus />
          {/* Keyboard shortcuts help modal */}
          <KeyboardShortcuts />
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: "#1f2937",
                color: "#f3f4f6",
                border: "1px solid rgba(139, 92, 246, 0.3)",
                borderRadius: "12px",
                maxWidth: "500px",
                wordBreak: "break-word",
                whiteSpace: "normal",
              },
              success: {
                iconTheme: {
                  primary: "#10b981",
                  secondary: "#f3f4f6",
                },
              },
              error: {
                iconTheme: {
                  primary: "#ef4444",
                  secondary: "#f3f4f6",
                },
              },
            }}
          />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
