import { useState, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Camera,
  StopCircle,
  Image as ImageIcon,
  Loader2,
} from "lucide-react";

const BACKEND_URL = "https://facevision-ai-2yj1.onrender.com";

interface CameraCaptureProps {
  onResult: (data: any) => void;
}

export function CameraCapture({
  onResult,
}: CameraCaptureProps) {

  const { user } = useAuth();
  const [active, setActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // =========================================================
  // HANDLE BACKEND RESPONSE
  // =========================================================

  const processAnalysisResponse = async (
    res: Response,
    source: string
  ) => {
    let data: any = {};

    try {
      data = await res.json();
    } catch {
      throw new Error(
        `Invalid server response (${res.status}).`
      );
    }

    console.log(
      `${source} ANALYSIS RESPONSE:`,
      res.status,
      data
    );

    // HTTP error
    if (!res.ok) {
      throw new Error(
        data?.error ||
          data?.detail ||
          `Analysis failed (${res.status}).`
      );
    }

    /*
      Your backend may return the result in different structures.

      Supported examples:

      {
        success: true,
        age: "...",
        smile: "...",
        mask: "...",
        emotion: "..."
      }

      OR

      {
        success: true,
        result: {
          age: "...",
          smile: "...",
          mask: "...",
          emotion: "..."
        }
      }

      OR

      {
        result: {
          age: "...",
          ...
        }
      }
    */

    let analysisData = data;

    if (
      data?.result &&
      typeof data.result === "object"
    ) {
      analysisData = {
        ...data.result,
        image_path:
          data.image_path ??
          data.result.image_path,
        message:
          data.message ??
          data.result.message,
        music:
          data.music ??
          data.result.music,
      };
    } else if (
      data?.data &&
      typeof data.data === "object"
    ) {
      analysisData = {
        ...data.data,
        image_path:
          data.image_path ??
          data.data.image_path,
        message:
          data.message ??
          data.data.message,
        music:
          data.music ??
          data.data.music,
      };
    } else if (
      data?.analysis &&
      typeof data.analysis === "object"
    ) {
      analysisData = {
        ...data.analysis,
        image_path:
          data.image_path ??
          data.analysis.image_path,
        message:
          data.message ??
          data.analysis.message,
        music:
          data.music ??
          data.analysis.music,
      };
    }

    /*
      Preserve useful top-level fields.
    */
    analysisData = {
      ...analysisData,

      age:
        analysisData.age ??
        data.age ??
        "N/A",

      smile:
        analysisData.smile ??
        data.smile ??
        "N/A",

      mask:
        analysisData.mask ??
        data.mask ??
        "N/A",

      emotion:
        analysisData.emotion ??
        data.emotion ??
        "N/A",

      image_path:
        analysisData.image_path ??
        data.image_path ??
        null,

      message:
        analysisData.message ??
        data.message ??
        null,

      music:
        analysisData.music ??
        data.music ??
        [],
    };

    console.log(
      `${source} NORMALIZED RESULT:`,
      analysisData
    );

    // Make sure we actually received an analysis
    const hasAnalysis =
      analysisData.age !== "N/A" ||
      analysisData.smile !== "N/A" ||
      analysisData.mask !== "N/A" ||
      analysisData.emotion !== "N/A";

    if (!hasAnalysis) {
      console.error(
        "Unexpected backend response:",
        data
      );

      throw new Error(
        "The server returned successfully, but no analysis result was found."
      );
    }

    // IMPORTANT:
    // Update the page
    setResult(analysisData);

    // Update parent/dashboard
    onResult(analysisData);

    return analysisData;
  };

  // =========================================================
  // START CAMERA
  // =========================================================

  const startCamera = async () => {
    try {
      if (
        !navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia
      ) {
        alert(
          "Camera access is not supported by this browser."
        );
        return;
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "user",
            width: {
              ideal: 1280,
            },
            height: {
              ideal: 720,
            },
          },
          audio: false,
        });

      streamRef.current = stream;

      if (!videoRef.current) {
        stream
          .getTracks()
          .forEach((track) => track.stop());

        return;
      }

      const video = videoRef.current;

      video.srcObject = stream;
      video.muted = true;
      video.playsInline = true;

      await video.play();

      setActive(true);

      console.log(
        "CAMERA STARTED:",
        video.videoWidth,
        "x",
        video.videoHeight
      );
    } catch (err) {
      console.error(
        "CAMERA START ERROR:",
        err
      );

      alert(
        "Unable to access the camera. Please allow camera permission and try again."
      );

      streamRef.current
        ?.getTracks()
        .forEach((track) => track.stop());

      streamRef.current = null;

      setActive(false);
    }
  };

  // =========================================================
  // STOP CAMERA
  // =========================================================

  const stopCamera = () => {
    streamRef.current
      ?.getTracks()
      .forEach((track) => track.stop());

    streamRef.current = null;

    setActive(false);
  };

  // =========================================================
  // CAPTURE CAMERA IMAGE
  // =========================================================

  const capture = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) {
      alert("Camera is not ready.");
      return;
    }

    if (
      video.readyState < 2 ||
      video.videoWidth === 0 ||
      video.videoHeight === 0
    ) {
      alert(
        "Camera is still starting. Please wait a moment and try again."
      );
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    if (!ctx) {
      alert(
        "Unable to create image capture."
      );
      return;
    }

    ctx.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    const blob =
      await new Promise<Blob | null>(
        (resolve) => {
          canvas.toBlob(
            (imageBlob) =>
              resolve(imageBlob),
            "image/jpeg",
            0.85
          );
        }
      );

    if (!blob) {
      alert(
        "Unable to create captured image."
      );
      return;
    }

    console.log(
      "CAPTURED IMAGE:",
      blob.size,
      "bytes",
      canvas.width,
      "x",
      canvas.height
    );

    const formData = new FormData();

formData.append(
  "file",
  blob,
  "camera-capture.jpg"
);

if (user?.email) {
  formData.append("user_email", user.email);
}
    setLoading(true);

    try {
      const res = await fetch(
        `${BACKEND_URL}/analyze`,
        {
          method: "POST",
          body: formData,
        }
      );

      await processAnalysisResponse(
        res,
        "CAMERA"
      );
    } catch (err) {
      console.error(
        "CAMERA ANALYSIS ERROR:",
        err
      );

      const message =
        err instanceof Error
          ? err.message
          : "Camera analysis failed.";

      alert(message);
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // SELECT FILE
  // =========================================================

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      alert(
        "Please select an image file."
      );

      e.target.value = "";
      return;
    }

    console.log(
      "FILE SELECTED:",
      file.name,
      file.size,
      file.type
    );

    setSelectedFile(file);
  };

  // =========================================================
  // UPLOAD IMAGE
  // =========================================================

  const uploadImage = async () => {
    if (!selectedFile) {
      alert(
        "Please select an image first."
      );
      return;
    }

    console.log(
      "UPLOADING FILE:",
      selectedFile.name,
      selectedFile.size,
      selectedFile.type
    );

    const formData = new FormData();

formData.append(
  "file",
  selectedFile,
  selectedFile.name
);

if (user?.email) {
  formData.append("user_email", user.email);
}

    setLoading(true);

    try {
      const res = await fetch(
        `${BACKEND_URL}/analyze`,
        {
          method: "POST",
          body: formData,
        }
      );

      await processAnalysisResponse(
        res,
        "FILE"
      );
    } catch (err) {
      console.error(
        "IMAGE ANALYSIS ERROR:",
        err
      );

      const message =
        err instanceof Error
          ? err.message
          : "Image analysis failed.";

      alert(message);
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-10">

      {/* =====================================================
          LEFT SIDE
          ===================================================== */}

      <div className="space-y-6">

        {/* CAMERA CARD */}

        <Card className="p-6 shadow-xl rounded-2xl">

          <h2 className="text-xl font-semibold mb-4">
            Live Camera Analysis
          </h2>

          {/* CAMERA PREVIEW */}

          <div className="relative h-[360px] rounded-xl overflow-hidden bg-black">

            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${
                !active
                  ? "hidden"
                  : ""
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

          <canvas
            ref={canvasRef}
            className="hidden"
          />

          {/* CAMERA BUTTONS */}

          <div className="flex justify-center gap-4 mt-6">

            {!active ? (
              <Button
                onClick={startCamera}
                disabled={loading}
              >
                <Camera className="mr-2" />
                Start Camera
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={stopCamera}
                  disabled={loading}
                >
                  <StopCircle className="mr-2" />
                  Stop
                </Button>

                <Button
                  onClick={capture}
                  disabled={loading}
                >
                  <ImageIcon className="mr-2" />
                  Capture
                </Button>
              </>
            )}

          </div>

        </Card>

        {/* =================================================
            UPLOAD CARD
            ================================================= */}

        <Card className="p-6 shadow-xl rounded-2xl">

          <h2 className="text-xl font-semibold mb-4">
            Upload Image
          </h2>

          <p className="text-center text-muted-foreground mb-4">
            Or upload an image from your device
          </p>

          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="w-full mb-4"
            disabled={loading}
          />

          {selectedFile && (
            <div className="mb-4 p-3 rounded-lg bg-muted">

              <p className="text-sm font-medium">
                Selected image:
              </p>

              <p className="text-sm text-muted-foreground break-all">
                {selectedFile.name}
              </p>

              <p className="text-xs text-muted-foreground mt-1">
                {(
                  selectedFile.size /
                  1024
                ).toFixed(1)} KB
              </p>

            </div>
          )}

          <Button
            onClick={uploadImage}
            disabled={
              !selectedFile ||
              loading
            }
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <ImageIcon className="mr-2" />
                Analyze Uploaded Image
              </>
            )}
          </Button>

        </Card>

      </div>

      {/* =====================================================
          RIGHT SIDE - RESULTS
          ===================================================== */}

      <Card className="p-6 shadow-xl rounded-2xl">

        <h2 className="text-xl font-semibold mb-4">
          Analysis Result
        </h2>

        {!result ? (
          <div className="text-center mt-20">

            <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />

            <p className="text-muted-foreground">
              Capture an image or upload an image to see results.
            </p>

          </div>
        ) : (
          <div className="space-y-5">

            {/* RESULT IMAGE */}

            {result.image_path && (
              <img
                src={`${BACKEND_URL}${result.image_path}`}
                alt="Analysis result"
                className="w-full h-64 object-contain rounded-lg bg-black"
              />
            )}

            {/* RESULT DETAILS */}

            <div className="grid grid-cols-2 gap-4">

              {/* AGE */}

              <div className="border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">
                  Age
                </p>

                <p className="text-lg font-semibold mt-1">
                  {result.age ?? "N/A"}
                </p>
              </div>

              {/* EMOTION */}

              <div className="border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">
                  Emotion
                </p>

                <p className="text-lg font-semibold mt-1 capitalize">
                  {result.emotion ?? "N/A"}
                </p>
              </div>

              {/* SMILE */}

              <div className="border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">
                  Smile
                </p>

                <p className="text-lg font-semibold mt-1">
                  {result.smile ?? "N/A"}
                </p>
              </div>

              {/* MASK */}

              <div className="border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">
                  Mask
                </p>

                <p className="text-lg font-semibold mt-1">
                  {result.mask ?? "N/A"}
                </p>
              </div>

            </div>

            {/* MESSAGE */}

            {result.message && (
              <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                <p className="font-semibold text-green-700">
                  {result.message}
                </p>
              </div>
            )}

            {/* MUSIC */}

            {Array.isArray(result.music) &&
              result.music.length > 0 && (
                <div className="mt-4">

                  <h3 className="font-semibold text-lg mb-3">
                    🎵 Peaceful Music Recommendations
                  </h3>

                  <div className="space-y-3">

                    {result.music.map(
                      (
                        m: any,
                        i: number
                      ) => (
                        <div
                          key={i}
                          className="border rounded-lg p-3 flex justify-between items-center"
                        >

                          <div>
                            <p className="font-medium">
                              {m.name}
                            </p>
                          </div>

                          {m.url && (
                            <a
                              href={m.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
                            >
                              ▶ Play
                            </a>
                          )}

                        </div>
                      )
                    )}

                  </div>

                </div>
              )}

          </div>
        )}

      </Card>

    </div>
  );
}