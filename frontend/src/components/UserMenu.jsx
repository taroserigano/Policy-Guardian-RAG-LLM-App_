/**
 * User Menu Component
 * Displays user avatar and dropdown menu with profile options.
 */
import { useState, useRef, useEffect, useCallback, memo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { User, Settings, LogOut, ChevronDown } from "lucide-react";
import toast from "react-hot-toast";

function UserMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = useCallback(async () => {
    await logout();
    toast.success("Logged out successfully");
    navigate("/login");
  }, [logout, navigate]);

  const handleToggleMenu = useCallback(() => {
    setIsOpen(!isOpen);
  }, [isOpen]);

  // Not authenticated - don't show anything
  if (!isAuthenticated) {
    return null;
  }

  // Get initials for avatar
  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || "U";

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={handleToggleMenu}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] hover:border-violet-500/30 transition-all duration-200"
      >
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
          <span className="text-xs font-bold text-white">{initials}</span>
        </div>

        {/* Name (hidden on mobile) */}
        <span className="hidden sm:block text-sm text-[var(--text-secondary)] max-w-[120px] truncate">
          {user?.full_name || user?.email?.split("@")[0]}
        </span>

        <ChevronDown
          className={`h-4 w-4 text-[var(--text-muted)] transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-subtle)] shadow-xl shadow-black/20 py-1 z-50 animate-slideUp">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
            <p className="text-sm font-medium text-[var(--text-primary)] truncate">
              {user?.full_name || "User"}
            </p>
            <p className="text-xs text-[var(--text-muted)] truncate">
              {user?.email}
            </p>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <Link
              to="/profile"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-3 px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--hover-bg)] transition-colors"
            >
              <Settings className="h-4 w-4" />
              <span>Settings</span>
            </Link>

            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(UserMenu);
