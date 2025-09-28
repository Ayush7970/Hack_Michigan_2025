"use client";

import { useState } from "react";
import { jsPDF } from "jspdf";

export default function GeneratePdfPage() {
  const [isWorking, setIsWorking] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [fetchedText, setFetchedText] = useState<string>(""); // ✅ hold fetched (now beautified) text

  const handleGenerate = async () => {
    try {
      setIsWorking(true);
      setStatus("Fetching text…");

      const res = await fetch("/api/conversation", { method: "GET" });
      if (!res.ok) throw new Error(`Backend error (${res.status})`);
      const txt = await res.text();

      // ✅ NEW: send to Gemini to beautify
      setStatus("Beautifying with Gemini…");
      const beautRes = await fetch("/api/beautify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: txt }),
      });

      // If beautify fails, fall back to original
      const beautified = beautRes.ok ? await beautRes.text() : txt;

      // ✅ print it to console AND store in state for on-page verification
      console.log("Beautified text:", beautified);
      setFetchedText(beautified);

      setStatus("Building PDF…");

      // Build the PDF
      const doc = new jsPDF({ unit: "pt", format: "a4" });
      const marginX = 48; // left/right
      const marginY = 60; // top
      const lineHeight = 16;
      const pageWidth = doc.internal.pageSize.getWidth();
      const usableWidth = pageWidth - marginX * 2;
      const pageHeight = doc.internal.pageSize.getHeight();

      doc.setFont("helvetica", "normal");
      doc.setFontSize(12);

      // 🔁 Only change here: feed beautified text into the PDF
      const lines = doc.splitTextToSize(beautified, usableWidth) as string[];
      let cursorY = marginY;

      for (const line of lines) {
        if (cursorY + lineHeight > pageHeight - marginY) {
          doc.addPage();
          cursorY = marginY;
        }
        doc.text(line, marginX, cursorY);
        cursorY += lineHeight;
      }

      setStatus("Saving PDF…");
      const filename = "from-text.pdf";
      doc.save(filename);

      // Optional preview
      const blobUrl = doc.output("bloburl");
      window.open(blobUrl, "_blank");

      setStatus("Done!");
    } catch (err: any) {
      console.error(err);
      setStatus(err?.message ?? "Something went wrong");
    } finally {
      setIsWorking(false);
      setTimeout(() => setStatus(null), 2000);
    }
  };

  return (
    <main className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl rounded-2xl border border-gray-800 p-6">
        <h1 className="text-xl font-semibold mb-2">Generate PDF from Backend Text</h1>
        <p className="text-sm text-gray-400 mb-6">
          Click the button to fetch text from{" "}
          <code className="text-gray-300">/api/placeholder</code> and convert it to a PDF.
        </p>

        <button
          onClick={handleGenerate}
          disabled={isWorking}
          className={`px-4 py-2 rounded-xl font-medium ${
            isWorking ? "bg-gray-700 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-500"
          }`}
        >
          {isWorking ? "Working…" : "Create PDF from Backend"}
        </button>

        {status && (
          <div className="mt-4 text-sm text-gray-300">
            Status: <span className="text-gray-100">{status}</span>
          </div>
        )}

        {/* ✅ Verification block: shows exactly what was used for the PDF */}
        {fetchedText && (
          <div className="mt-4">
            <div className="text-sm text-gray-400 mb-2">Beautified text (preview):</div>
            <pre className="text-xs bg-gray-900 border border-gray-800 p-3 rounded overflow-auto max-h-64">
{fetchedText}
            </pre>
          </div>
        )}
      </div>
    </main>
  );
}