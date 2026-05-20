import React, { createContext, useContext, useEffect, useRef, useState } from "react";

const AuthContext = createContext(null);

/**
 * Provides global authentication state and methods to the React application.
 * Manages token persistence via localStorage and auto-hydrates User state.
 *
 * @param {Object} props - Component props.
 * @param {React.ReactNode} props.children - Child components wrapped by context.
 * @returns {JSX.Element} The populated AuthContext Provider.
 */
export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [token, setToken]     = useState(() => localStorage.getItem("token"));
  const [loading, setLoading] = useState(!!localStorage.getItem("token")); // only true if there's a token to verify
  const skipVerify = useRef(false); // set to true after a fresh login/register so we don't re-hit /auth/me

  // Verify stored token on mount only (not after login/register)
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    if (skipVerify.current) {
      skipVerify.current = false;
      setLoading(false);
      return;
    }
    fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setUser(data.user))
      .catch(() => {
        localStorage.removeItem("token");
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  /**
   * Internal helper to persist token and user payload locally.
   *
   * @param {string} t - The JWT token.
   * @param {Object} userData - User profile payload dictionary.
   */
  const _persist = (t, userData) => {
    skipVerify.current = true; // we already have the user — skip /auth/me round-trip
    localStorage.setItem("token", t);
    setToken(t);
    setUser(userData);
  };

  /**
   * Authenticates a user against the API and persists their JWT.
   *
   * @param {string} email - The user's login email.
   * @param {string} password - The user's password.
   * @returns {Promise<Object>} The authenticated user object data.
   * @throws {Error} If authentication fails.
   */
  const login = async (email, password) => {
    const res  = await fetch("/api/auth/login", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    _persist(data.token, data.user);
    return data.user;
  };

  /**
   * Registers a new user account via the API.
   *
   * @param {string} name - Full name of the new user.
   * @param {string} email - Unregistered email address.
   * @param {string} password - Secure string at least 8 chars long.
   * @returns {Promise<Object>} The newly created user object data.
   * @throws {Error} If registration fails (e.g. email exists).
   */
  const register = async (name, email, password) => {
    const res  = await fetch("/api/auth/register", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    _persist(data.token, data.user);
    return data.user;
  };

  /**
   * Clears the active authentication session and removes tokens from local storage.
   *
   * @returns {void}
   */
  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  /**
   * Patches the user's demographic profile data remotely and locally.
   *
   * @param {Object} profileData - A dictionary of new demographic key-values.
   * @returns {Promise<Object>} The updated user profile object.
   * @throws {Error} If the server rejects the update.
   */
  const updateProfile = async (profileData) => {
    const res  = await fetch("/api/auth/profile", {
      method:  "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization:  `Bearer ${token}`,
      },
      body: JSON.stringify(profileData),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Update failed");
    setUser(data.user);
    return data.user;
  };

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, register, logout, updateProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * React Hook providing access to global user, auth status, and auth actions.
 *
 * @returns {Object} An object containing user state and methods (`user, login, logout`, etc.)
 */
export const useAuth = () => useContext(AuthContext);
