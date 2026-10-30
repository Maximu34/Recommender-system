import { useCallback, useRef, useState } from 'react';

/**
 * Microphone capture for humming.
 *
 * MediaRecorder gives webm/opus in Chrome and Firefox; Safari gives mp4. The
 * backend decodes with PyAV, which handles all of them, so nothing is
 * converted here. `level` drives the waveform and is the only reason the Web
 * Audio graph exists -- it tells the user the mic is actually hearing them.
 *
 * getUserMedia requires a secure context: localhost during development, HTTPS
 * once deployed.
 */
export function useRecorder(maxMs = 10_000) {
  const [recording, setRecording] = useState(false);
  const [level, setLevel] = useState<number[]>([]);
  const [elapsed, setElapsed] = useState(0);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number | null>(null);
  const stopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const resolveRef = useRef<((b: Blob | null) => void) | null>(null);
  const startedRef = useRef(0);

  const cleanup = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (stopTimerRef.current) clearTimeout(stopTimerRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    rafRef.current = null;
    stopTimerRef.current = null;
  }, []);

  const stop = useCallback(() => {
    recorderRef.current?.state === 'recording' && recorderRef.current.stop();
  }, []);

  const start = useCallback(async (): Promise<Blob | null> => {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error(
        'This browser cannot record audio. Microphone access needs a secure ' +
          'context — use localhost or an https:// address.',
      );
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    ctx.createMediaStreamSource(stream).connect(analyser);
    const buf = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteTimeDomainData(buf);
      let peak = 0;
      for (const v of buf) peak = Math.max(peak, Math.abs(v - 128) / 128);
      setLevel((prev) => [...prev.slice(-59), peak]);
      setElapsed((Date.now() - startedRef.current) / 1000);
      rafRef.current = requestAnimationFrame(tick);
    };

    const rec = new MediaRecorder(stream);
    recorderRef.current = rec;
    chunksRef.current = [];
    rec.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
    rec.onstop = () => {
      void ctx.close();
      cleanup();
      setRecording(false);
      const blob = chunksRef.current.length
        ? new Blob(chunksRef.current, { type: rec.mimeType })
        : null;
      resolveRef.current?.(blob);
      resolveRef.current = null;
    };

    setLevel([]);
    setElapsed(0);
    startedRef.current = Date.now();
    rec.start();
    setRecording(true);
    tick();
    stopTimerRef.current = setTimeout(stop, maxMs);

    return new Promise<Blob | null>((resolve) => {
      resolveRef.current = resolve;
    });
  }, [cleanup, maxMs, stop]);

  return { recording, level, elapsed, start, stop };
}
