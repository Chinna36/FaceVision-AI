import React, {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

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
  createContext<AuthContextType | undefined>(
    undefined
  );

/* ============================================================
   PROVIDER
   ============================================================ */

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] =
    useState<User | null>(null);

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
     NORMALIZE ANALYTICS
     ========================================================== */

  const normalizeAnalytics = (
    data: any
  ): Analytics => {
    return {
      happy: Number(data?.happy || 0),
      sad: Number(data?.sad || 0),
      angry: Number(data?.angry || 0),
      fear: Number(data?.fear || 0),
      neutral: Number(data?.neutral || 0),
    };
  };

  /* ==========================================================
     LOAD DATABASE HISTORY
     ========================================================== */

  const loadDatabaseHistory = async (
    currentUser: User
  ): Promise<boolean> => {
    try {
      const encodedEmail =
        encodeURIComponent(
          currentUser.email
        );

      /* ------------------------------------------------------
         LOAD HISTORY
         ------------------------------------------------------ */

      const historyResponse =
        await fetch(
          `${BACKEND_URL}/analysis-history?user_email=${encodedEmail}`
        );

      if (!historyResponse.ok) {
        throw new Error(
          `History request failed: ${historyResponse.status}`
        );
      }

      const historyData =
        await historyResponse.json();

      /* ------------------------------------------------------
         ACCEPT DIFFERENT BACKEND RESPONSE SHAPES
         ------------------------------------------------------ */

      let history: any[] = [];

      if (Array.isArray(historyData)) {
        history = historyData;
      } else if (
        Array.isArray(historyData.history)
      ) {
        history = historyData.history;
      } else if (
        Array.isArray(historyData.results)
      ) {
        history = historyData.results;
      }

      /* ------------------------------------------------------
         LOAD ANALYTICS
         ------------------------------------------------------ */

      const analyticsResponse =
        await fetch(
          `${BACKEND_URL}/analysis-analytics?user_email=${encodedEmail}`
        );

      if (!analyticsResponse.ok) {
        throw new Error(
          `Analytics request failed: ${analyticsResponse.status}`
        );
      }

      const analyticsData =
        await analyticsResponse.json();

      let databaseAnalytics =
        defaultAnalytics;

      if (
        analyticsData &&
        analyticsData.analytics
      ) {
        databaseAnalytics =
          normalizeAnalytics(
            analyticsData.analytics
          );
      } else {
        databaseAnalytics =
          normalizeAnalytics(
            analyticsData
          );
      }

      /* ------------------------------------------------------
         UPDATE REACT STATE
         ------------------------------------------------------ */

      setCapturedResults(history);

      setAnalytics(
        databaseAnalytics
      );

      /* ------------------------------------------------------
         ALSO CACHE DATABASE DATA LOCALLY
         ------------------------------------------------------ */

      localStorage.setItem(
        `analytics_${currentUser.id}`,
        JSON.stringify(
          databaseAnalytics
        )
      );

      localStorage.setItem(
        `results_${currentUser.id}`,
        JSON.stringify(history)
      );

      console.log(
        "Database history loaded:",
        history.length
      );

      console.log(
        "Database analytics loaded:",
        databaseAnalytics
      );

      return true;
    } catch (error) {
      console.error(
        "Could not load database analysis history:",
        error
      );

      return false;
    }
  };

  /* ==========================================================
     LOAD LOCAL DATA
     ========================================================== */

  const loadLocalData = (
    currentUser: User
  ) => {
    try {
      const a =
        localStorage.getItem(
          `analytics_${currentUser.id}`
        );

      const r =
        localStorage.getItem(
          `results_${currentUser.id}`
        );

      const s =
        localStorage.getItem(
          `settings_${currentUser.id}`
        );

      if (a) {
        setAnalytics(
          normalizeAnalytics(
            JSON.parse(a)
          )
        );
      } else {
        setAnalytics(
          defaultAnalytics
        );
      }

      if (r) {
        const parsedResults =
          JSON.parse(r);

        setCapturedResults(
          Array.isArray(
            parsedResults
          )
            ? parsedResults
            : []
        );
      } else {
        setCapturedResults([]);
      }

      if (s) {
        setSettings(
          JSON.parse(s)
        );
      } else {
        setSettings(
          defaultSettings
        );
      }
    } catch (error) {
      console.error(
        "Error loading local data:",
        error
      );

      setAnalytics(
        defaultAnalytics
      );

      setCapturedResults([]);

      setSettings(
        defaultSettings
      );
    }
  };

  /* ==========================================================
     LOAD USER SESSION
     ========================================================== */

  useEffect(() => {
    const restoreSession =
      async () => {
        try {
          const storedUser =
            localStorage.getItem(
              "current_user"
            );

          if (!storedUser) {
            return;
          }

          const parsedUser: User =
            JSON.parse(
              storedUser
            );

          setUser(parsedUser);

          /* ----------------------------------------------
             Load local data immediately.
             This keeps the UI responsive.
             ---------------------------------------------- */

          loadLocalData(
            parsedUser
          );

          /* ----------------------------------------------
             Then load the database data.
             Database becomes the source of truth.
             ---------------------------------------------- */

          await loadDatabaseHistory(
            parsedUser
          );
        } catch (error) {
          console.error(
            "Error loading saved session:",
            error
          );

          localStorage.removeItem(
            "current_user"
          );

          setUser(null);
        }
      };

    restoreSession();
  }, []);

  /* ==========================================================
     LOGIN
     ========================================================== */

  const login = async (
    email: string,
    password: string
  ): Promise<boolean> => {
    try {
      const response =
        await fetch(
          `${BACKEND_URL}/login`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              email: email
                .trim()
                .toLowerCase(),
              password,
            }),
          }
        );

      let data: any = {};

      try {
        data =
          await response.json();
      } catch {
        throw new Error(
          `Server returned an invalid response (${response.status}).`
        );
      }

      if (
        !response.ok ||
        !data.success
      ) {
        console.error(
          "Login failed:",
          response.status,
          data
        );

        if (
          response.status === 401
        ) {
          return false;
        }

        throw new Error(
          data.detail ||
            data.message ||
            `Login failed with status ${response.status}.`
        );
      }

      const loggedInUser: User =
        data.user;

      if (!loggedInUser) {
        throw new Error(
          "Server login response did not contain a user."
        );
      }

      /* ------------------------------------------------------
         SET USER
         ------------------------------------------------------ */

      setUser(loggedInUser);

      localStorage.setItem(
        "current_user",
        JSON.stringify(
          loggedInUser
        )
      );

      /* ------------------------------------------------------
         LOAD LOCAL DATA FIRST
         ------------------------------------------------------ */

      loadLocalData(
        loggedInUser
      );

      /* ------------------------------------------------------
         THEN LOAD DATABASE DATA
         ------------------------------------------------------ */

      await loadDatabaseHistory(
        loggedInUser
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
      const response =
        await fetch(
          `${BACKEND_URL}/register`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              fullName,
              email,
              password,
              guardianEmail,
            }),
          }
        );

      const data =
        await response.json();

      if (
        !response.ok ||
        !data.success
      ) {
        console.error(
          "Registration failed:",
          data
        );

        return false;
      }

      const registeredUser: User =
        data.user;

      setUser(
        registeredUser
      );

      localStorage.setItem(
        "current_user",
        JSON.stringify(
          registeredUser
        )
      );

      setAnalytics(
        defaultAnalytics
      );

      setCapturedResults([]);

      setSettings(
        defaultSettings
      );

      localStorage.setItem(
        `analytics_${registeredUser.id}`,
        JSON.stringify(
          defaultAnalytics
        )
      );

      localStorage.setItem(
        `results_${registeredUser.id}`,
        JSON.stringify([])
      );

      localStorage.setItem(
        `settings_${registeredUser.id}`,
        JSON.stringify(
          defaultSettings
        )
      );

      /* ------------------------------------------------------
         New account should have empty database history.
         ------------------------------------------------------ */

      await loadDatabaseHistory(
        registeredUser
      );

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
        JSON.stringify(
          analytics
        )
      );

      localStorage.setItem(
        `results_${user.id}`,
        JSON.stringify(
          capturedResults
        )
      );

      localStorage.setItem(
        `settings_${user.id}`,
        JSON.stringify(
          settings
        )
      );
    }

    setUser(null);

    setAnalytics(
      defaultAnalytics
    );

    setCapturedResults([]);

    setSettings(
      defaultSettings
    );

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

    const emotion =
      String(
        result?.emotion ||
          "neutral"
      ).toLowerCase();

    const validEmotion: Emotion =
      [
        "happy",
        "sad",
        "angry",
        "fear",
        "neutral",
      ].includes(emotion)
        ? (emotion as Emotion)
        : "neutral";

    /* ------------------------------------------------------
       UPDATE ANALYTICS IMMEDIATELY
       ------------------------------------------------------ */

    const updatedAnalytics: Analytics =
      {
        ...analytics,
        [validEmotion]:
          (analytics[
            validEmotion
          ] || 0) + 1,
      };

    /* ------------------------------------------------------
       CREATE RESULT
       ------------------------------------------------------ */

    const newResult = {
      ...result,
      timestamp:
        result?.timestamp ||
        new Date().toISOString(),
    };

    const updatedResults = [
      newResult,
      ...capturedResults,
    ];

    /* ------------------------------------------------------
       UPDATE UI
       ------------------------------------------------------ */

    setAnalytics(
      updatedAnalytics
    );

    setCapturedResults(
      updatedResults
    );

    /* ------------------------------------------------------
       CACHE LOCALLY
       ------------------------------------------------------ */

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

    console.log(
      "Analysis result added to UI:",
      newResult
    );

    /*
      IMPORTANT:
      The backend /analyze endpoint already saves
      the analysis into analysis_history.

      Therefore we DO NOT POST the result again here,
      otherwise every analysis could be duplicated.
    */
  };

  /* ==========================================================
     THEME TOGGLE
     ========================================================== */

  const toggleTheme = () => {
    const newTheme =
      settings.theme === "dark"
        ? "light"
        : "dark";

    const updatedSettings: Settings =
      {
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