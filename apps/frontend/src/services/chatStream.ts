/** UTF-8 SSE v2 frames. A disconnected reader never cancels the producer. */
export type ChatFrame = Record<string, unknown> & { v: 2; type: string };
export async function readChatEvents(response: Response, receive: (frame: ChatFrame) => Promise<void> | void) {
  if (!response.body || !response.headers.get("Content-Type")?.startsWith("text/event-stream")) {
    throw new Error("stream_invalid");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  const encoder = new TextEncoder();
  let buffered = "";
  let afterCr = false;
  const normalize = (value: string) => {
    let normalized = "";
    for (const character of value) {
      if (character === "\n" && afterCr) { afterCr = false; continue; }
      afterCr = character === "\r";
      normalized += afterCr ? "\n" : character;
    }
    return normalized;
  };
  const consume = async (raw: string) => {
    if (encoder.encode(raw).length > 65536) throw new Error("frame_limit");
    let type = "message";
    const data: string[] = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) type = line.slice(6).trim();
      if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
    }
    if (!data.length) return;
    const value: unknown = JSON.parse(data.join("\n"));
    if (!value || typeof value !== "object" || Array.isArray(value) || !("v" in value) || value.v !== 2) {
      throw new Error("frame_invalid");
    }
    if ("type" in value && value.type !== type) throw new Error("frame_invalid");
    await receive({ ...value, v: 2, type });
  };
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffered += normalize(decoder.decode(value, { stream: !done }));
      let end: number;
      while ((end = buffered.indexOf("\n\n")) >= 0) {
        await consume(buffered.slice(0, end));
        buffered = buffered.slice(end + 2);
      }
      if (encoder.encode(buffered).length > 65536) throw new Error("frame_limit");
      if (done) {
        if (buffered.trim() && !buffered.trim().startsWith(":")) throw new Error("stream_incomplete");
        return;
      }
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
