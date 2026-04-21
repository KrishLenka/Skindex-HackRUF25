import React, { createContext, useContext, useEffect, useRef, useState } from "react";

const AuthContext = createContext(null);

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

  const _persist = (t, userData) => {
    skipVerify.current = true; // we already have the user — skip /auth/me round-trip
    localStorage.setItem("token", t);
    setToken(t);
    setUser(userData);
  };

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

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

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

export const useAuth = () => useContext(AuthContext);
