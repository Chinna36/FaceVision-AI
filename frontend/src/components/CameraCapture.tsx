import { useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Camera,
  StopCircle,
  Image as ImageIcon,
  Loader2
} from "lucide-react";

const BACKEND_URL = "http://127.0.0.1:8000";

interface CameraCaptureProps {
  onResult: (data: any) => void;
}

export function CameraCapture({ onResult }: CameraCaptureProps) {
  const [active, setActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
        await videoRef.current.play();
        streamRef.current = stream;
        setActive(true);
      }
    } catch (err) {
      alert("Camera access denied");
      console.error(err);
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    setActive(false);
  };

  const capture = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx?.drawImage(videoRef.current, 0, 0);

    const blob = await new Promise<Blob>(resolve =>
      canvas.toBlob(b => resolve(b!), "image/jpeg")
    );

    const formData = new FormData();
    formData.append("file", blob, "capture.jpg");

    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      setResult(data);
      onResult(data);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  const uploadImage = async () => {
  if (!selectedFile) {
    alert("Please select an image first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  setLoading(true);

  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    setResult(data);
    onResult(data);
  } catch (err) {
    console.error(err);
    alert("Image analysis failed.");
  }

  setLoading(false);
};

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-10">

      {/* CAMERA PANEL */}
      <Card className="p-6 shadow-xl rounded-2xl">
        <h2 className="text-xl font-semibold mb-4">
          Live Camera Analysis
        </h2>

        <div className="relative h-[360px] rounded-xl overflow-hidden bg-black">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover ${
              !active ? "hidden" : ""
            }`}
          />

          {!active && (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              Camera preview will appear here
            </div>
          )}

          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
              <Loader2 className="animate-spin h-8 w-8 text-white" />
            </div>
          )}
        </div>

        <canvas ref={canvasRef} className="hidden" />

        <div className="flex justify-center gap-4 mt-6">
          {!active ? (
            <Button onClick={startCamera}>
              <Camera className="mr-2" /> Start Camera
            </Button>
          ) : (
            <>
              <Button variant="outline" onClick={stopCamera}>
                <StopCircle className="mr-2" /> Stop
              </Button>
              <Button onClick={capture}>
                <ImageIcon className="mr-2" /> Capture
              </Button>
            </>
          )}
        </div>
      </Card>

      {/* Upload Image */}

    <div className="mt-6 border-t pt-6">

      <p className="text-center font-medium mb-4">
        OR Upload an Image
      </p>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0]);
          }
        }}
        className="mb-4"
      />

      <Button
        onClick={uploadImage}
        disabled={!selectedFile}
        className="w-full"
      >
        Analyze Uploaded Image
      </Button>

    </div>

      {/* RESULT PANEL */}
      <Card className="p-6 shadow-xl rounded-2xl">
        <h2 className="text-xl font-semibold mb-4">
          Analysis Result
        </h2>

        {!result ? (
          <p className="text-muted-foreground text-center mt-20">
            Capture an image to see results
          </p>
        ) : (
          <>
            <img
              src={`${BACKEND_URL}${result.image_path}`}
              className="w-full h-48 object-contain rounded-lg mb-4 bg-black"
            />

            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <p><b>Age:</b> {result.age}</p>
              <p><b>Emotion:</b> {result.emotion}</p>
              <p><b>Smile:</b> {result.smile}</p>
              <p><b>Mask:</b> {result.mask}</p>
            </div>

            <p className="font-semibold text-green-600 mb-4">
              {result.message}
            </p>

            {result.music?.length > 0 && (
            <div className="mt-4">
              <h3 className="font-semibold text-lg mb-3">
                🎵 Peaceful Music Recommendations
              </h3>

              <div className="space-y-3">
                {result.music.map((m: any, i: number) => (
                  <div
                    key={i}
                    className="border rounded-lg p-3 flex justify-between items-center"
                  >
                    <div>
                      <p className="font-medium">{m.name}</p>
                    </div>

                    <a
                      href={m.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
                    >
                      ▶ Play
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
          </>
        )}
      </Card>
    </div>
  );
}
