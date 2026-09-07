import React, { createContext, useContext, useEffect, useState } from "react";

/* ============================================================
   TYPES
   ============================================================ */

type Emotion =
  | "happy"
  | "sad"
  | "angry"
  | "fear"
  | "neutral";

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

interface User {
  id: string;
  fullName: string;
  email: string;
  guardianEmail?: string | null;
}

interface AuthContextType {
  user: User | null;
  analytics: Analytics;
  settings: Settings;
  capturedResults: any[];
  isAuthenticated: boolean;

  login: (
    email: string,
    password: string
  ) => Promise<boolean>;

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

/* ============================================================
   BACKEND
   ============================================================ */

const BACKEND_URL =
  "https://facevision-ai-2yj1.onrender.com";

/* ============================================================
   DEFAULTS
   ============================================================ */

const defaultAnalytics: Analytics = {
  happy: 0,
  sad: 0,
  angry: 0,
  fear: 0,
  neutral: 0,
};

const defaultSettings: Settings = {
  theme: "dark",
};

/* ============================================================
   CONTEXT
   ============================================================ */

const AuthContext =
  createContext<AuthContextType | undefined>(undefined);

/* ============================================================
   PROVIDER
   ============================================================ */

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);

  const [analytics, setAnalytics] =
    useState<Analytics>(defaultAnalytics);

  const [settings, setSettings] =
    useState<Settings>(defaultSettings);

  const [capturedResults, setCapturedResults] =
    useState<any[]>([]);

  /* ==========================================================
     APPLY THEME
     ========================================================== */

  useEffect(() => {
    document.documentElement.classList.remove(
      "dark",
      "light"
    );

    document.documentElement.classList.add(
      settings.theme
    );
  }, [settings.theme]);

  /* ==========================================================
     LOAD USER SESSION
     ========================================================== */

  useEffect(() => {
    try {
      const storedUser =
        localStorage.getItem("current_user");

      if (!storedUser) {
        return;
      }

      const parsedUser: User =
        JSON.parse(storedUser);

      setUser(parsedUser);

      const a = localStorage.getItem(
        `analytics_${parsedUser.id}`
      );

      const r = localStorage.getItem(
        `results_${parsedUser.id}`
      );

      const s = localStorage.getItem(
        `settings_${parsedUser.id}`
      );

      if (a) {
        setAnalytics(JSON.parse(a));
      } else {
        setAnalytics(defaultAnalytics);
      }

      if (r) {
        setCapturedResults(JSON.parse(r));
      } else {
        setCapturedResults([]);
      }

      if (s) {
        setSettings(JSON.parse(s));
      } else {
        setSettings(defaultSettings);
      }
    } catch (error) {
      console.error(
        "Error loading saved session:",
        error
      );

      localStorage.removeItem("current_user");
      setUser(null);
    }
  }, []);

  /* ==========================================================
     LOGIN
     ========================================================== */

  const login = async (
  email: string,
  password: string
): Promise<boolean> => {
  try {
    const response = await fetch(
      `${BACKEND_URL}/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
        }),
      }
    );

    let data: any = {};

    try {
      data = await response.json();
    } catch {
      throw new Error(
        `Server returned an invalid response (${response.status}).`
      );
    }

    if (!response.ok || !data.success) {
      console.error(
        "Login failed:",
        response.status,
        data
      );

      // Actual invalid credentials
      if (response.status === 401) {
        return false;
      }

      // Other backend errors should NOT look
      // like an invalid password.
      throw new Error(
        data.detail ||
        data.message ||
        `Login failed with status ${response.status}.`
      );
    }

    const loggedInUser: User = data.user;

    if (!loggedInUser) {
      throw new Error(
        "Server login response did not contain a user."
      );
    }

    setUser(loggedInUser);

    localStorage.setItem(
      "current_user",
      JSON.stringify(loggedInUser)
    );

    const a = localStorage.getItem(
      `analytics_${loggedInUser.id}`
    );

    const r = localStorage.getItem(
      `results_${loggedInUser.id}`
    );

    const s = localStorage.getItem(
      `settings_${loggedInUser.id}`
    );

    setAnalytics(
      a
        ? JSON.parse(a)
        : defaultAnalytics
    );

    setCapturedResults(
      r
        ? JSON.parse(r)
        : []
    );

    setSettings(
      s
        ? JSON.parse(s)
        : defaultSettings
    );

    return true;

  } catch (error) {
    console.error(
      "Login request error:",
      error
    );

    throw error;
  }
};

  /* ==========================================================
     REGISTER
     ========================================================== */

  const register = async (
    fullName: string,
    email: string,
    password: string,
    guardianEmail?: string
  ): Promise<boolean> => {
    try {
      const response = await fetch(
        `${BACKEND_URL}/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            fullName,
            email,
            password,
            guardianEmail,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        console.error(
          "Registration failed:",
          data
        );

        return false;
      }

      const registeredUser: User =
        data.user;

      setUser(registeredUser);

      localStorage.setItem(
        "current_user",
        JSON.stringify(registeredUser)
      );

      setAnalytics(defaultAnalytics);

      setCapturedResults([]);

      setSettings(defaultSettings);

      return true;
    } catch (error) {
      console.error(
        "Registration request error:",
        error
      );

      return false;
    }
  };

  /* ==========================================================
     LOGOUT
     ========================================================== */

  const logout = () => {
    if (user) {
      localStorage.setItem(
        `analytics_${user.id}`,
        JSON.stringify(analytics)
      );

      localStorage.setItem(
        `results_${user.id}`,
        JSON.stringify(capturedResults)
      );

      localStorage.setItem(
        `settings_${user.id}`,
        JSON.stringify(settings)
      );
    }

    setUser(null);

    setAnalytics(defaultAnalytics);

    setCapturedResults([]);

    setSettings(defaultSettings);

    localStorage.removeItem(
      "current_user"
    );
  };

  /* ==========================================================
     ANALYSIS HANDLER
     ========================================================== */

  const addAnalysisResult = (
    result: any
  ) => {
    if (!user) {
      return;
    }

    const emotion: Emotion =
      (result.emotion || "neutral")
        .toLowerCase();

    const validEmotion: Emotion =
      [
        "happy",
        "sad",
        "angry",
        "fear",
        "neutral",
      ].includes(emotion)
        ? emotion
        : "neutral";

    const updatedAnalytics = {
      ...analytics,
      [validEmotion]:
        (analytics[validEmotion] || 0) + 1,
    };

    const updatedResults = [
      {
        ...result,
        timestamp:
          new Date().toISOString(),
      },
      ...capturedResults,
    ];

    setAnalytics(
      updatedAnalytics
    );

    setCapturedResults(
      updatedResults
    );

    localStorage.setItem(
      `analytics_${user.id}`,
      JSON.stringify(
        updatedAnalytics
      )
    );

    localStorage.setItem(
      `results_${user.id}`,
      JSON.stringify(
        updatedResults
      )
    );
  };

  /* ==========================================================
     THEME TOGGLE
     ========================================================== */

  const toggleTheme = () => {
    const newTheme =
      settings.theme === "dark"
        ? "light"
        : "dark";

    const updatedSettings = {
      theme: newTheme,
    };

    setSettings(
      updatedSettings
    );

    if (user) {
      localStorage.setItem(
        `settings_${user.id}`,
        JSON.stringify(
          updatedSettings
        )
      );
    }
  };

  /* ==========================================================
     PROVIDER
     ========================================================== */

  return (
    <AuthContext.Provider
      value={{
        user,
        analytics,
        settings,
        capturedResults,
        isAuthenticated:
          !!user,

        login,
        register,
        logout,
        addAnalysisResult,
        toggleTheme,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/* ============================================================
   HOOK
   ============================================================ */

export function useAuth() {
  const ctx =
    useContext(AuthContext);

  if (!ctx) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return ctx;
}