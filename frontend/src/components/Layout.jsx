/**
 * Layout component with navigation and common structure.
 * Modern dark theme with glassmorphism effects.
 */
import { Link, useLocation } from "react-router-dom";
import { FileText, MessageSquare, Sparkles, Zap, Circle } from "lucide-react";

export default function Layout({ children }) {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-[#09090b] relative overflow-hidden">
      {/* Animated background - Subtle aurora effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Primary gradient orbs */}
        <div className="absolute -top-[40%] -right-[20%] w-[800px] h-[800px] rounded-full bg-gradient-to-br from-violet-600/20 via-purple-600/10 to-transparent blur-[120px] animate-pulse-soft" />
        <div
          className="absolute top-[20%] -left-[20%] w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-indigo-600/15 via-blue-600/10 to-transparent blur-[100px] animate-pulse-soft"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute -bottom-[30%] right-[10%] w-[500px] h-[500px] rounded-full bg-gradient-to-tl from-fuchsia-600/10 via-pink-600/5 to-transparent blur-[80px] animate-pulse-soft"
          style={{ animationDelay: "2s" }}
        />

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,black_40%,transparent_100%)]" />
      </div>

      {/* Top Navigation */}
      <nav className="relative z-10 border-b border-white/[0.04] bg-[#09090b]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo/Title */}
            <Link to="/" className="flex items-center group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-xl blur-lg opacity-40 group-hover:opacity-60 transition-all duration-500" />
                <div className="relative bg-gradient-to-br from-violet-500 to-fuchsia-500 p-2.5 rounded-xl shadow-lg">
                  <Zap className="h-5 w-5 text-white" />
                </div>
              </div>
              <div className="ml-3.5">
                <h1 className="text-lg font-bold tracking-tight">
                  <span className="text-white">Policy</span>
                  <span className="gradient-text-vibrant">RAG</span>
                </h1>
                <p className="text-[10px] text-zinc-500 font-medium tracking-wide uppercase">
                  AI Intelligence
                </p>
              </div>
            </Link>

            {/* Navigation Links */}
            <div className="flex items-center gap-1">
              <Link
                to="/upload"
                className={`relative flex items-center px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive("/upload")
                    ? "text-white"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                {isActive("/upload") && (
                  <div className="absolute inset-0 bg-gradient-to-r from-violet-500/15 to-fuchsia-500/15 rounded-xl border border-violet-500/20" />
                )}
                <FileText
                  className={`relative h-4 w-4 mr-2 ${isActive("/upload") ? "text-violet-400" : ""}`}
                />
                <span className="relative">Upload</span>
              </Link>

              <Link
                to="/chat"
                className={`relative flex items-center px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive("/chat")
                    ? "text-white"
                    : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                {isActive("/chat") && (
                  <div className="absolute inset-0 bg-gradient-to-r from-violet-500/15 to-fuchsia-500/15 rounded-xl border border-violet-500/20" />
                )}
                <MessageSquare
                  className={`relative h-4 w-4 mr-2 ${isActive("/chat") ? "text-violet-400" : ""}`}
                />
                <span className="relative">Chat</span>
                <Sparkles className="relative h-3 w-3 ml-1.5 text-amber-400" />
              </Link>

              {/* Divider */}
              <div className="w-px h-6 bg-white/[0.06] mx-2" />

              {/* Status indicator */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <div className="relative">
                  <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-20" />
                  <Circle className="relative h-2 w-2 text-emerald-400 fill-emerald-400" />
                </div>
                <span className="text-xs text-emerald-400 font-medium">
                  Online
                </span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
