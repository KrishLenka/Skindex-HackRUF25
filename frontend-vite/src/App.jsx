// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import { Activity, Upload, User, LogIn, MessageCircle } from "lucide-react";

import Home        from "@/components/home";
import ImageUpload from "@/components/ImageUpload";
import Login       from "@/components/Login";
import Profile     from "@/components/Profile";
import AIAssistant from "@/components/AIAssistant";
import { AuthProvider, useAuth } from "@/context/AuthContext";

/**
 * Route wrapper that enforces authentication.
 * Redirects unauthenticated users to the `/login` route.
 *
 * @param {Object} props - React props.
 * @param {React.ReactNode} props.children - The child components to render if authenticated.
 * @returns {React.ReactNode} Modifies the render tree based on auth state.
 */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-rose-50 via-orange-50 to-amber-100">
      <div className="w-8 h-8 border-4 border-rose-300 border-t-rose-600 rounded-full animate-spin" />
    </div>
  );
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

/**
 * Global application header containing branding and navigation links.
 * Automatically adapts UI based on current user authenticated state.
 *
 * @returns {JSX.Element} The Header component.
 */
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="relative">
      <div className="absolute inset-0 bg-gradient-to-b from-rose-50 via-orange-50 to-amber-100" />
      <div className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 h-40 w-[36rem] rounded-full bg-white/50 blur-2xl opacity-60" />

      <div className="relative border-b border-rose-200/70 backdrop-blur-sm">
        <div className="w-full px-4">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-rose-600 rounded-lg flex items-center justify-center mr-4 shadow-sm">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-rose-900 leading-tight">DermAI</h1>
                <p className="text-sm text-rose-800/80 leading-tight">Your trusted AI dermatology consultant</p>
              </div>
            </div>

            {/* Auth controls */}
            {user ? (
              <div className="flex items-center gap-3 text-sm">
                <span className="text-rose-700 font-medium hidden sm:block">
                  Hi, {user.name.split(" ")[0]}
                </span>
                <Link
                  to="/profile"
                  className="flex items-center gap-1.5 bg-rose-100 hover:bg-rose-200 text-rose-800 px-3 py-1.5 rounded-lg font-medium transition-colors"
                >
                  <User className="w-4 h-4" /> Profile
                </Link>
              </div>
            ) : (
              <Link
                to="/login"
                className="flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium shadow transition-colors"
              >
                <LogIn className="w-4 h-4" /> Sign in
              </Link>
            )}
          </div>

          <nav className="border-t border-rose-200/70 py-2">
            <div className="flex space-x-6 text-sm">
              <Link to="/" className="text-rose-900/90 hover:text-rose-900 font-medium py-2">
                Home
              </Link>
              <Link to="/analyze" className="flex items-center gap-1.5 text-rose-900/90 hover:text-rose-900 font-medium py-2">
                <Upload className="w-4 h-4" /> Image Analysis
              </Link>
              <Link to="/assistant" className="flex items-center gap-1.5 text-rose-900/90 hover:text-rose-900 font-medium py-2">
                <MessageCircle className="w-4 h-4" /> AI Assistant
              </Link>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

/**
 * The root Application component routing the Skindex frontend.
 * Provides global contexts (Auth) and top-level navigation structure.
 *
 * @returns {JSX.Element} The root application routing structure.
 */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Header />
        <Routes>
          <Route path="/"        element={<Home />} />
          <Route path="/analyze"    element={<ImageUpload />} />
          <Route path="/assistant"  element={<AIAssistant />} />
          <Route path="/login"      element={<Login />} />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

