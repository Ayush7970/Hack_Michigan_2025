import { NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

// Ensure Node.js runtime so fs is available
export const runtime = "nodejs";

// Optional: allow ?file=conv_123.json (defaults to your file)
function getFileNameFromSearch(search: string | null) {
  if (!search) return "conv_1759052779.json";
  try {
    const sp = new URLSearchParams(search);
    const f = sp.get("file");
    if (!f) return "conv_1759052779.json";
    // basic safety: only allow .json files residing under conversations
    if (!/^[\w\-]+\.json$/.test(f)) return "conv_1759052779.json";
    return f;
  } catch {
    return "conv_1759052779.json";
  }
}

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const fileName = getFileNameFromSearch(url.search);

    // process.cwd() here is .../frontend
    const filePath = path.resolve(
      process.cwd(),        // .../frontend
      "..",                 // go up to project root
      "Backend",
      "conversations",
      fileName
    );

    // (Optional) quick existence check with a helpful error
    await fs.access(filePath);

    const fileContent = await fs.readFile(filePath, "utf-8");
    return new NextResponse(fileContent, {
      status: 200,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    });
  } catch (err: any) {
    // Return helpful diagnostics so you can see what's wrong
    const msg = {
      error: "Failed to read conversation file",
      details: err?.message,
      cwd: process.cwd(),
      expectedPath: path.resolve(process.cwd(), "..", "Backend", "conversations", "conv_1759052779.json"),
      hint: "Check path, filename, and that the route runs with runtime='nodejs'.",
    };
    return new NextResponse(JSON.stringify(msg, null, 2), {
      status: 500,
      headers: { "Content-Type": "application/json; charset=utf-8" },
    });
  }
}
