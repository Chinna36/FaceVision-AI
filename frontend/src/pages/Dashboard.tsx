import { useAuth } from "@/contexts/AuthContext";
import { Navbar } from "@/components/Navbar";
import { AnalyticsCard } from "@/components/AnalyticsCard";
import { Smile, Frown, Angry, AlertTriangle } from "lucide-react";

export default function Dashboard() {
  const { user, analytics } = useAuth();

  return (
    <div className="app-background min-h-screen">
      <Navbar />

      <main className="container mx-auto px-6 py-12">

        {/* HERO SECTION */}
        <section className="mb-16">
          <h1 className="text-5xl font-extrabold tracking-tight mb-4">
            FaceVision AI
          </h1>

          <p className="text-muted-foreground text-lg max-w-2xl">
            An intelligent facial emotion recognition system that analyzes
            real-time expressions and delivers personalized insights using AI.
          </p>

          <p className="text-muted-foreground text-lg max-w-2xl mt-2">
            Capture emotions, understand mood patterns, and enhance awareness.
          </p>

          <div className="mt-6 text-xl">
            Welcome,
            <span className="ml-2 font-semibold gradient-text">
              {user?.fullName?.split(" ")[0]}
            </span>
          </div>
        </section>

        {/* ANALYTICS SUMMARY */}
        <section>
          <h2 className="text-2xl font-semibold mb-8">
            Emotion Intelligence Summary
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-10">

            <AnalyticsCard
              title="Happy"
              value={analytics.happy}
              icon={Smile}
              color="success"
            />

            <AnalyticsCard
              title="Sad"
              value={analytics.sad}
              icon={Frown}
              color="primary"
            />

            <AnalyticsCard
              title="Angry"
              value={analytics.angry}
              icon={Angry}
              color="warning"
            />

            <AnalyticsCard
              title="Fear"
              value={analytics.fear}
              icon={AlertTriangle}
              color="destructive"
            />

          </div>
        </section>

      </main>
    </div>
  );
}
