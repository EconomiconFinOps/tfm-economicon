import { describe, expect, it } from "vitest";
import { readChatEvents, type ChatFrame } from "../src/services/chatStream";

function stream(bytes: Uint8Array[]) {
  return new Response(new ReadableStream<Uint8Array>({
    start(controller) { for (const chunk of bytes) controller.enqueue(chunk); controller.close(); }
  }), { headers: { "Content-Type": "text/event-stream; charset=utf-8" } });
}
const encode = (text: string) => new TextEncoder().encode(text);

describe("Framing SSE propio cerrado JUP-035", () => {
  it.each(["\n", "\r\n", "\r"])("admite comentarios, data multilínea y bytes UTF-8 partidos con terminador %j", async delimiter => {
    const bytes = encode("\uFEFF: heartbeat" + delimiter + "id: op:attempt:1" + delimiter +
      "event: delta" + delimiter + 'data: {"v":2,"type":"delta",' + delimiter +
      'data: "text":"🌍"}' + delimiter + delimiter);
    const frames: ChatFrame[] = [];
    await readChatEvents(stream(Array.from(bytes, byte => new Uint8Array([byte]))), frame => { frames.push(frame); });
    expect(frames).toEqual([{ v: 2, type: "delta", text: "🌍" }]);
  });
  it("no convierte EOF de un frame sin delimitador en confirmación", async () => {
    const frames: ChatFrame[] = [];
    await expect(readChatEvents(stream([encode('event: final\ndata: {"v":2,"type":"final"}')]),
      frame => { frames.push(frame); })).rejects.toThrow("stream_incomplete");
    expect(frames).toEqual([]);
  });
  it("rechaza UTF-8 inválido antes de entregar datos al runtime", async () => {
    const frames: ChatFrame[] = [];
    await expect(readChatEvents(stream([new Uint8Array([0xc3, 0x28])]),
      frame => { frames.push(frame); })).rejects.toThrow();
    expect(frames).toEqual([]);
  });
  it("rechaza UTF-8 inválido dentro de un frame que por lo demás es JSON válido", async () => {
    const frames: ChatFrame[] = [];
    await expect(readChatEvents(stream([encode('event: delta\ndata: {"v":2,"type":"delta","text":"'),
      new Uint8Array([0xc3, 0x28]), encode('"}\n\n')]),
      frame => { frames.push(frame); })).rejects.toThrow();
    expect(frames).toEqual([]);
  });
  it("rechaza un frame sobre64KiB sin truncarlo", async () => {
    const frames: ChatFrame[] = [];
    await expect(readChatEvents(stream([encode('event: delta\ndata: ' + JSON.stringify({ v: 2, type: "delta", text: "x".repeat(65536) }) + '\n\n')]),
      frame => { frames.push(frame); })).rejects.toThrow("frame_limit");
    expect(frames).toEqual([]);
  });
});
