/**
 * Layout component with navigation and common structure.
 * Supports dark/light theme with glassmorphism effects.
 * Mobile responsive with hamburger menu.
 */
import { useState, useEffect } from "react";
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

  const isActive = (path) => location.pathname === path;

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

      {/* Top Navigation */}
      <nav className="relative z-10 border-b border-[var(--border-subtle)] bg-[var(--bg-primary)]/80 backdrop-blur-xl transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 md:h-16">
            {/* Logo/Title */}
            <Link to="/" className="flex items-center group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-xl blur-lg opacity-40 group-hover:opacity-60 transition-all duration-500" />
                <div className="relative bg-gradient-to-br from-violet-500 to-fuchsia-500 p-2 md:p-2.5 rounded-xl shadow-lg">
                  <Zap className="h-4 w-4 md:h-5 md:w-5 text-white" />
                </div>
              </div>
              <div className="ml-2.5 md:ml-3.5">
                <h1 className="text-base md:text-lg font-bold tracking-tight">
                  <span className="text-[var(--text-primary)]">Policy</span>
                  <span className="gradient-text-vibrant">RAG</span>
                </h1>
                <p className="text-[9px] md:text-[10px] text-[var(--text-secondary)] font-semibold tracking-wide uppercase hidden sm:block">
                  AI Intelligence
                </p>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <div className="hidden md:flex items-center gap-1">
              <Link
                to="/upload"
                className={`relative flex items-center px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive("/upload")
                    ? "text-[var(--text-primary)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
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
                    ? "text-[var(--text-primary)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
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

              <Link
                to="/compliance"
                className={`relative flex items-center px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive("/compliance")
                    ? "text-[var(--text-primary)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)]"
                }`}
              >
                {isActive("/compliance") && (
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/15 to-cyan-500/15 rounded-xl border border-emerald-500/20" />
                )}
                <ShieldCheck
                  className={`relative h-4 w-4 mr-2 ${isActive("/compliance") ? "text-emerald-400" : ""}`}
                />
                <span className="relative">Compliance</span>
              </Link>

              {/* Divider */}
              <div className="w-px h-6 bg-[var(--border-subtle)] mx-2" />

              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--hover-bg)] transition-all duration-200"
                title={
                  theme === "dark"
                    ? "Switch to light mode"
                    : "Switch to dark mode"
                }
              >
                {theme === "dark" ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </button>

              {/* User Menu */}
              <UserMenu />

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

            {/* Mobile: Status + Menu Button */}
            <div className="flex md:hidden items-center gap-2">
              {/* Mobile status dot */}
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <Circle className="h-2 w-2 text-emerald-400 fill-emerald-400" />
              </div>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="mobile-menu-btn"
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
