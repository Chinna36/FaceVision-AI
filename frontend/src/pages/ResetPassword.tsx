import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const BACKEND_URL = "https://facevision-ai-2yj1.onrender.com";

export default function ResetPassword() {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as {
    email?: string;
    code?: string;
  } | null;

  const email = state?.email || "";
  const code = state?.code || "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (!email || !code) {
      setError(
        "Reset session is missing. Please start the Forgot Password process again."
      );
      return;
    }

    if (!newPassword || !confirmPassword) {
      setError("Please enter your new password in both fields.");
      return;
    }

    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(`${BACKEND_URL}/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          code: code,
          newPassword: newPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMessage = "Unable to reset password.";

        if (typeof data?.detail === "string") {
          errorMessage = data.detail;
        } else if (data?.detail) {
          errorMessage =
            data.detail.message ||
            data.detail.error ||
            JSON.stringify(data.detail);
        } else if (typeof data?.message === "string") {
          errorMessage = data.message;
        }

        throw new Error(errorMessage);
      }

      setMessage(
        "Password reset successful! Redirecting you to the login page..."
      );

      setNewPassword("");
      setConfirmPassword("");

      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err: any) {
      console.error("RESET PASSWORD ERROR:", err);

      setError(
        typeof err?.message === "string"
          ? err.message
          : "Unable to connect to the server. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "20px",
        background: "#050b16",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "450px",
          padding: "32px",
          borderRadius: "16px",
          background: "#0d1726",
          border: "1px solid #26364d",
          boxShadow: "0 10px 35px rgba(0,0,0,0.35)",
          boxSizing: "border-box",
        }}
      >
        <h2
          style={{
            textAlign: "center",
            marginBottom: "10px",
            color: "#ffffff",
          }}
        >
          Set New Password
        </h2>

        <p
          style={{
            textAlign: "center",
            color: "#aebbd0",
            marginBottom: "25px",
          }}
        >
          Enter your new password below.
        </p>

        {email && (
          <p
            style={{
              textAlign: "center",
              fontSize: "14px",
              color: "#aebbd0",
              marginBottom: "20px",
            }}
          >
            Resetting password for{" "}
            <strong style={{ color: "#ffffff" }}>{email}</strong>
          </p>
        )}

        {error && (
          <div
            style={{
              padding: "12px",
              marginBottom: "18px",
              borderRadius: "8px",
              background: "#3a1518",
              border: "1px solid #8f3038",
              color: "#ffb4b4",
              fontSize: "14px",
            }}
          >
            {error}
          </div>
        )}

        {message && (
          <div
            style={{
              padding: "12px",
              marginBottom: "18px",
              borderRadius: "8px",
              background: "#12351f",
              border: "1px solid #2c8a4b",
              color: "#9ff0b8",
              fontSize: "14px",
            }}
          >
            {message}
          </div>
        )}

        <form onSubmit={handleResetPassword}>
          <div style={{ marginBottom: "18px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "8px",
                fontWeight: 600,
                color: "#ffffff",
              }}
            >
              New Password
            </label>

            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password"
              autoComplete="new-password"
              disabled={loading}
              style={{
                width: "100%",
                padding: "13px",
                borderRadius: "8px",
                border: "1px solid #41516a",
                background: "#080f1c",
                color: "#ffffff",
                boxSizing: "border-box",
                outline: "none",
              }}
            />
          </div>

          <div style={{ marginBottom: "22px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "8px",
                fontWeight: 600,
                color: "#ffffff",
              }}
            >
              Confirm New Password
            </label>

            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              autoComplete="new-password"
              disabled={loading}
              style={{
                width: "100%",
                padding: "13px",
                borderRadius: "8px",
                border: "1px solid #41516a",
                background: "#080f1c",
                color: "#ffffff",
                boxSizing: "border-box",
                outline: "none",
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "13px",
              border: "none",
              borderRadius: "8px",
              background: "#16c4b5",
              color: "#061019",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "16px",
              fontWeight: 700,
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Resetting Password..." : "Set New Password"}
          </button>
        </form>

        <div
          style={{
            textAlign: "center",
            marginTop: "20px",
          }}
        >
          <button
            type="button"
            onClick={() => navigate("/login")}
            style={{
              border: "none",
              background: "transparent",
              color: "#16c4b5",
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}