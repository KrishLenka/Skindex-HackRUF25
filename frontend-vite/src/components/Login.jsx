import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

/**
 * Manages dual authentication flows for existing users (Login) and new users (Register).
 * Handles input validation, visibility toggling for passwords, and session hydration.
 *
 * @returns {JSX.Element} The Login/Register view component.
 */
export default function Login() {
  const { login, register } = useAuth();
  const navigate             = useNavigate();

  const [mode, setMode]         = useState("login"); // "login" | "register"
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [error, setError]       = useState("");
  const [busy, setBusy]         = useState(false);

  /**
   * Clears the current form state payload and error boundary.
   */
  const reset = () => {
    setError("");
    setName("");
    setEmail("");
    setPassword("");
    setConfirm("");
  };

  /**
   * Switches the active flow between Login and Register modes, zeroing out form state.
   */
  const toggleMode = () => {
    reset();
    setMode((m) => (m === "login" ? "register" : "login"));
  };

  /**
   * Validates form input locally before routing credentials to the authentication API context.
   *
   * @param {React.FormEvent} e - Form event.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (mode === "register") {
      if (password !== confirm) {
        setError("Passwords do not match");
        return;
      }
      if (password.length < 8) {
        setError("Password must be at least 8 characters");
        return;
      }
    }

    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      navigate("/profile");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-orange-50 to-amber-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-rose-200/60 p-8">
          {/* Logo */}
          <div className="flex items-center justify-center mb-6 gap-3">
            <div className="w-11 h-11 bg-rose-600 rounded-xl flex items-center justify-center shadow">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xl font-bold text-rose-900">DermAI</p>
              <p className="text-xs text-rose-700/70">AI Dermatology Consultant</p>
            </div>
          </div>

          {/* Mode title */}
          <h2 className="text-center text-2xl font-bold text-rose-900 mb-1">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h2>
          <p className="text-center text-sm text-rose-700/70 mb-6">
            {mode === "login"
              ? "Sign in to your DermAI account"
              : "Start your skin health journey"}
          </p>

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name — register only */}
            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium text-rose-800 mb-1">
                  Full name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Smith"
                  className="w-full rounded-lg border border-rose-200 bg-white px-3 py-2.5 text-sm text-rose-900 placeholder-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400"
                />
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-rose-800 mb-1">
                Email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-lg border border-rose-200 bg-white px-3 py-2.5 text-sm text-rose-900 placeholder-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-rose-800 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "register" ? "Min. 8 characters" : "••••••••"}
                  className="w-full rounded-lg border border-rose-200 bg-white px-3 py-2.5 pr-10 text-sm text-rose-900 placeholder-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute inset-y-0 right-3 flex items-center text-rose-400 hover:text-rose-600"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm password — register only */}
            {mode === "register" && (
              <div>
                <label className="block text-sm font-medium text-rose-800 mb-1">
                  Confirm password
                </label>
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Re-enter password"
                  className="w-full rounded-lg border border-rose-200 bg-white px-3 py-2.5 text-sm text-rose-900 placeholder-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400"
                />
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={busy}
              className="w-full mt-2 rounded-lg bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {busy
                ? "Please wait…"
                : mode === "login"
                ? "Sign in"
                : "Create account"}
            </button>
          </form>

          {/* Toggle mode */}
          <p className="mt-5 text-center text-sm text-rose-700/80">
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={toggleMode}
              className="font-semibold text-rose-700 hover:text-rose-900 underline underline-offset-2"
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
