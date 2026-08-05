import { Moon, Sun, LogOut, LayoutDashboard, Camera, User, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { NavLink } from "@/components/NavLink";

export function Navbar() {
  const { user, logout, toggleTheme, settings } = useAuth();

  return (
    <header className="border-b sticky top-0 z-50 bg-background/80 backdrop-blur">
      <div className="container mx-auto flex justify-between items-center h-16 px-4">

        {/* LOGO */}
        <h1 className="font-bold text-xl gradient-text">
          FaceVision AI
        </h1>

        {/* NAV LINKS */}
        <nav className="flex items-center gap-6">

          <NavLink
            to="/dashboard"
            className="flex items-center gap-2 text-sm text-muted-foreground"
            activeClassName="text-primary font-semibold"
          >
            <LayoutDashboard size={16} />
            Dashboard
          </NavLink>

          <NavLink
            to="/detection"
            className="flex items-center gap-2 text-sm text-muted-foreground"
            activeClassName="text-primary font-semibold"
          >
            <Camera size={16} />
            Detection
          </NavLink>

          <NavLink
            to="/profile"
            className="flex items-center gap-2 text-sm text-muted-foreground"
            activeClassName="text-primary font-semibold"
          >
            <User size={16} />
            Profile
          </NavLink>

          <NavLink
            to="/settings"
            className="flex items-center gap-2 text-sm text-muted-foreground"
            activeClassName="text-primary font-semibold"
          >
            <Settings size={16} />
            Settings
          </NavLink>

        </nav>

        {/* RIGHT ACTIONS */}
        <div className="flex items-center gap-4">

          {/* THEME TOGGLE */}
          <Button variant="ghost" size="icon" onClick={toggleTheme}>
            {settings.theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </Button>

          {/* USER NAME */}
          <span className="text-sm font-medium">
            {user?.fullName}
          </span>

          {/* LOGOUT */}
          <Button variant="destructive" size="sm" onClick={logout}>
            <LogOut className="mr-1 h-4 w-4" />
            Logout
          </Button>

        </div>
      </div>
    </header>
  );
}
