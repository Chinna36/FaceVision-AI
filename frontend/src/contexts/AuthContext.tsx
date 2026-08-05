import React, { createContext, useContext, useEffect, useState } from "react";

/* ================= TYPES ================= */

type Emotion = "happy" | "sad" | "angry" | "fear" | "neutral";

interface Analytics {
  happy: number;
  sad: number;
  angry: number;
  fear: number;
  neutral: number;
}

interface Settings {
  theme: "dark" | "light";
}

interface AuthContextType {
  user: any;
  analytics: Analytics;
  settings: Settings;
  capturedResults: any[];
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (
    fullName: string,
    email: string,
    password: string,
    guardianEmail?: string
  ) => Promise<boolean>;
  logout: () => void;
  addAnalysisResult: (result: any) => void;
  toggleTheme: () => void;
}

/* ================= DEFAULTS ================= */

const defaultAnalytics: Analytics = {
  happy: 0,
  sad: 0,
  angry: 0,
  fear: 0,
  neutral: 0
};

const defaultSettings: Settings = {
  theme: "dark"
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/* ================= PROVIDER ================= */

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [analytics, setAnalytics] = useState<Analytics>(defaultAnalytics);
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [capturedResults, setCapturedResults] = useState<any[]>([]);

  /* ===== APPLY THEME ===== */
  useEffect(() => {
    document.documentElement.classList.remove("dark", "light");
    document.documentElement.classList.add(settings.theme);
  }, [settings.theme]);

  /* ===== LOAD USER SESSION ===== */
  useEffect(() => {
    const storedUser = localStorage.getItem("current_user");
    if (!storedUser) return;

    const parsedUser = JSON.parse(storedUser);
    setUser(parsedUser);

    const a = localStorage.getItem(`analytics_${parsedUser.id}`);
    const r = localStorage.getItem(`results_${parsedUser.id}`);
    const s = localStorage.getItem(`settings_${parsedUser.id}`);

    if (a) setAnalytics(JSON.parse(a));
    if (r) setCapturedResults(JSON.parse(r));
    if (s) setSettings(JSON.parse(s));
  }, []);

  /* ===== LOGIN ===== */
  const login = async (email: string, password: string) => {
    const users = JSON.parse(localStorage.getItem("users") || "[]");
    const found = users.find(
      (u: any) => u.email === email && u.password === password
    );

    if (!found) return false;

    const { password: _, ...safeUser } = found;
    setUser(safeUser);
    localStorage.setItem("current_user", JSON.stringify(safeUser));

    const a = localStorage.getItem(`analytics_${safeUser.id}`);
    const r = localStorage.getItem(`results_${safeUser.id}`);
    const s = localStorage.getItem(`settings_${safeUser.id}`);

    setAnalytics(a ? JSON.parse(a) : defaultAnalytics);
    setCapturedResults(r ? JSON.parse(r) : []);
    setSettings(s ? JSON.parse(s) : defaultSettings);

    return true;
  };

  /* ===== REGISTER ===== */
  const register = async (
    fullName: string,
    email: string,
    password: string,
    guardianEmail?: string
  ) => {
    const users = JSON.parse(localStorage.getItem("users") || "[]");
    if (users.find((u: any) => u.email === email)) return false;

    const newUser = {
      id: crypto.randomUUID(),
      fullName,
      email,
      password,
      guardianEmail
    };

    users.push(newUser);
    localStorage.setItem("users", JSON.stringify(users));

    const { password: _, ...safeUser } = newUser;
    setUser(safeUser);
    localStorage.setItem("current_user", JSON.stringify(safeUser));

    setAnalytics(defaultAnalytics);
    setCapturedResults([]);
    setSettings(defaultSettings);

    return true;
  };

  /* ===== LOGOUT ===== */
  const logout = () => {
    if (user) {
      localStorage.setItem(`analytics_${user.id}`, JSON.stringify(analytics));
      localStorage.setItem(`results_${user.id}`, JSON.stringify(capturedResults));
      localStorage.setItem(`settings_${user.id}`, JSON.stringify(settings));
    }

    setUser(null);
    localStorage.removeItem("current_user");
  };

  /* ===== ANALYSIS HANDLER ===== */
  const addAnalysisResult = (result: any) => {
    if (!user) return;

    const emotion: Emotion =
      (result.emotion || "neutral").toLowerCase();

    const updatedAnalytics = {
      ...analytics,
      [emotion]: (analytics[emotion] || 0) + 1
    };

    const updatedResults = [
      { ...result, timestamp: new Date().toISOString() },
      ...capturedResults
    ];

    setAnalytics(updatedAnalytics);
    setCapturedResults(updatedResults);

    localStorage.setItem(`analytics_${user.id}`, JSON.stringify(updatedAnalytics));
    localStorage.setItem(`results_${user.id}`, JSON.stringify(updatedResults));
  };

  /* ===== THEME TOGGLE ===== */
  const toggleTheme = () => {
    const newTheme = settings.theme === "dark" ? "light" : "dark";
    const updated = { theme: newTheme };
    setSettings(updated);

    if (user) {
      localStorage.setItem(`settings_${user.id}`, JSON.stringify(updated));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        analytics,
        settings,
        capturedResults,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        addAnalysisResult,
        toggleTheme
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/* ================= HOOK ================= */

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
