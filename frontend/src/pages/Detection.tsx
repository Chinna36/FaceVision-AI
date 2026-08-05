import { useAuth } from "@/contexts/AuthContext";
import { Navbar } from "@/components/Navbar";
import { CameraCapture } from "@/components/CameraCapture";

export default function Detection() {
  const { addAnalysisResult } = useAuth();

  return (
    <div className="app-background min-h-screen">
      <Navbar />

      <main className="container mx-auto px-6 py-12">

        {/* HEADER */}
        <section className="mb-10">
          <h1 className="text-4xl font-bold mb-3">
            Emotion Detection
          </h1>

          <p className="text-muted-foreground text-lg max-w-xl">
            Capture your facial expressions in real time and receive emotion
            analysis, music recommendations, and insights instantly.
          </p>
        </section>

        {/* CAMERA + RESULTS */}
        <CameraCapture onResult={addAnalysisResult} />

      </main>
    </div>
  );
}
