/**
 * Layout component with navigation and common structure.
 * Supports dark/light theme with glassmorphism effects.
 * Mobile responsive with hamburger menu.
 */
import { useState, useEffect, useCallback, memo } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  FileText,
  MessageSquare,
  Sparkles,
  Zap,
  Circle,
  ShieldCheck,
  Moon,
  Sun,
  Menu,
  X,
} from "lucide-react";
import { useTheme } from "../contexts/ThemeContext";
import UserMenu from "./UserMenu";

export default function Layout({ children }) {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = useCallback(
    (path) => location.pathname === path,
    [location.pathname],
  );

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] relative overflow-hidden transition-colors duration-300">
      {/* Animated background - Subtle aurora effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Primary gradient orbs - smaller on mobile */}
        <div className="absolute -top-[40%] -right-[20%] w-[400px] md:w-[800px] h-[400px] md:h-[800px] rounded-full bg-gradient-to-br from-violet-600/20 via-purple-600/10 to-transparent blur-[80px] md:blur-[120px] animate-pulse-soft" />
        <div
          className="absolute top-[20%] -left-[20%] w-[300px] md:w-[600px] h-[300px] md:h-[600px] rounded-full bg-gradient-to-tr from-indigo-600/15 via-blue-600/10 to-transparent blur-[60px] md:blur-[100px] animate-pulse-soft"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute -bottom-[30%] right-[10%] w-[250px] md:w-[500px] h-[250px] md:h-[500px] rounded-full bg-gradient-to-tl from-fuchsia-600/10 via-pink-600/5 to-transparent blur-[50px] md:blur-[80px] animate-pulse-soft"
          style={{ animationDelay: "2s" }}
        />

        {/* Grid pattern overlay - only in dark mode */}
        {theme === "dark" && (
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] md:bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,black_40%,transparent_100%)]" />
        )}
      </div>

      {/* Top Navigation - Solid Glass Navbar */}
      <nav className="relative z-10 bg-gradient-to-r from-slate-900/95 via-purple-900/90 to-slate-900/95 backdrop-blur-2xl border-b border-purple-500/30 shadow-[0_0_50px_rgba(139,92,246,0.3)] transition-all duration-500">
        {/* Animated gradient border at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-violet-500 to-transparent" />
        {/* Inner glow */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 md:h-16">
            {/* Logo/Title */}
            <Link to="/" className="flex items-center group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 rounded-xl blur-xl opacity-70 group-hover:opacity-100 transition-all duration-500 scale-125" />
                <div className="relative bg-gradient-to-br from-violet-500 via-fuchsia-500 to-pink-500 p-2.5 md:p-3 rounded-xl shadow-2xl shadow-violet-500/50 border border-white/20">
                  <Zap className="h-5 w-5 md:h-6 md:w-6 text-white drop-shadow-lg" />
                </div>
              </div>
              <div className="ml-3 md:ml-4">
                <h1 className="text-lg md:text-xl font-black tracking-tight">
                  <span className="text-white">Policy</span>
                  <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent">
                    RAG
                  </span>
                </h1>
                <p className="text-[10px] md:text-xs text-purple-300/80 font-bold tracking-[0.2em] uppercase hidden sm:block">
                  AI Intelligence
                </p>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <div className="hidden md:flex items-center gap-2 bg-black/30 rounded-xl p-1.5 border border-white/10">
              <Link
                to="/upload"
                className={`relative flex items-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${
                  isActive("/upload")
                    ? "text-white"
                    : "text-purple-200/70 hover:text-white hover:bg-white/10"
                }`}
              >
                {isActive("/upload") && (
                  <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-lg shadow-lg shadow-violet-500/50" />
                )}
                <FileText className="relative h-4 w-4 mr-2" />
                <span className="relative">Upload</span>
              </Link>

              <Link
                to="/chat"
                className={`relative flex items-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${
                  isActive("/chat")
                    ? "text-white"
                    : "text-purple-200/70 hover:text-white hover:bg-white/10"
                }`}
              >
                {isActive("/chat") && (
                  <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-lg shadow-lg shadow-violet-500/50" />
                )}
                <MessageSquare className="relative h-4 w-4 mr-2" />
                <span className="relative">Chat</span>
              </Link>

              <Link
                to="/compliance"
                className={`relative flex items-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${
                  isActive("/compliance")
                    ? "text-white"
                    : "text-purple-200/70 hover:text-white hover:bg-white/10"
                }`}
              >
                {isActive("/compliance") && (
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-lg shadow-lg shadow-emerald-500/50" />
                )}
                <ShieldCheck className="relative h-4 w-4 mr-2" />
                <span className="relative">Compliance</span>
              </Link>
            </div>

            {/* Right side controls */}
            <div className="hidden md:flex items-center gap-3">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2.5 rounded-xl text-purple-200/70 hover:text-white bg-white/5 hover:bg-white/15 border border-white/10 hover:border-purple-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20"
                title={
                  theme === "dark"
                    ? "Switch to light mode"
                    : "Switch to dark mode"
                }
              >
                {theme === "dark" ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>

              {/* User Menu */}
              <UserMenu />

              {/* Status indicator */}
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border border-emerald-400/40 shadow-lg shadow-emerald-500/20">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <span className="text-sm text-emerald-300 font-bold tracking-wide">
                  Live
                </span>
              </div>
            </div>

            {/* Mobile: Status + Menu Button */}
            <div className="flex md:hidden items-center gap-3">
              {/* Mobile status dot */}
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-400/40">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              </div>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2.5 rounded-xl text-purple-200 bg-white/10 border border-white/20 hover:bg-white/20 transition-all"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation Overlay */}
      <div
        className={`mobile-nav-overlay md:hidden ${mobileMenuOpen ? "open" : ""}`}
        onClick={() => setMobileMenuOpen(false)}
      />

      {/* Mobile Navigation Drawer */}
      <div
        className={`mobile-nav-drawer md:hidden ${mobileMenuOpen ? "open" : ""}`}
      >
        <div className="p-4">
          {/* Mobile menu header */}
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--border-subtle)]">
            <div className="flex items-center">
              <div className="bg-gradient-to-br from-violet-500 to-fuchsia-500 p-2 rounded-xl">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <span className="ml-2 font-bold text-[var(--text-primary)]">
                Menu
              </span>
            </div>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Mobile navigation links */}
          <div className="space-y-2">
            <Link
              to="/upload"
              className={`mobile-nav-link ${isActive("/upload") ? "active" : ""}`}
            >
              <FileText
                className={`h-5 w-5 mr-3 ${isActive("/upload") ? "text-violet-400" : ""}`}
              />
              Upload Documents
            </Link>

            <Link
              to="/chat"
              className={`mobile-nav-link ${isActive("/chat") ? "active" : ""}`}
            >
              <MessageSquare
                className={`h-5 w-5 mr-3 ${isActive("/chat") ? "text-violet-400" : ""}`}
              />
              Chat
              <Sparkles className="h-3.5 w-3.5 ml-auto text-amber-400" />
            </Link>

            <Link
              to="/compliance"
              className={`mobile-nav-link ${isActive("/compliance") ? "active" : ""}`}
            >
              <ShieldCheck
                className={`h-5 w-5 mr-3 ${isActive("/compliance") ? "text-emerald-400" : ""}`}
              />
              Compliance Check
            </Link>
          </div>

          {/* Divider */}
          <div className="my-4 border-t border-[var(--border-subtle)]" />

          {/* Theme toggle */}
          <button onClick={toggleTheme} className="mobile-nav-link w-full">
            {theme === "dark" ? (
              <>
                <Sun className="h-5 w-5 mr-3 text-amber-400" />
                Light Mode
              </>
            ) : (
              <>
                <Moon className="h-5 w-5 mr-3 text-blue-400" />
                Dark Mode
              </>
            )}
          </button>

          {/* User section */}
          <div className="mt-4 pt-4 border-t border-[var(--border-subtle)]">
            <div className="flex items-center px-3 py-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-semibold">
                U
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  User
                </p>
                <p className="text-xs text-[var(--text-secondary)]">
                  Authenticated
                </p>
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="mt-4 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <div className="relative">
              <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-20" />
              <Circle className="relative h-2 w-2 text-emerald-400 fill-emerald-400" />
            </div>
            <span className="text-sm text-emerald-400 font-medium">
              System Online
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-8">
        {children}
      </main>
    </div>
  );
}
