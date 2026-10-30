import { useCallback, useEffect, useRef, useState } from 'react';

import { audioUrl, type Track } from '../api';

/**
 * A single <audio> element shared by the whole page.
 *
 * Plain media playback, not Web Audio: Apple's CDN serves the clips and a
 * media element loads cross-origin without needing CORS. (Apple does send
 * `Access-Control-Allow-Origin: *`, so Web Audio analysis would also work if
 * it were ever needed.)
 */
export function usePlayer() {
  const ref = useRef<HTMLAudioElement | null>(null);
  const [current, setCurrent] = useState<Track | null>(null);
  const [playing, setPlaying] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);

  if (ref.current === null && typeof Audio !== 'undefined') {
    ref.current = new Audio();
  }

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onTime = () => setPosition(el.currentTime);
    const onMeta = () => setDuration(el.duration || 0);
    const onEnd = () => {
      setPlaying(false);
      setPosition(0);
    };
    el.addEventListener('timeupdate', onTime);
    el.addEventListener('loadedmetadata', onMeta);
    el.addEventListener('ended', onEnd);
    el.addEventListener('play', () => setPlaying(true));
    el.addEventListener('pause', () => setPlaying(false));
    return () => {
      el.removeEventListener('timeupdate', onTime);
      el.removeEventListener('loadedmetadata', onMeta);
      el.removeEventListener('ended', onEnd);
    };
  }, []);

  const toggle = useCallback(
    (track: Track) => {
      const el = ref.current;
      if (!el) return;
      if (current?.id === track.id) {
        if (el.paused) void el.play();
        else el.pause();
        return;
      }
      el.src = audioUrl(track);
      setCurrent(track);
      setPosition(0);
      void el.play();
    },
    [current],
  );

  const stop = useCallback(() => {
    ref.current?.pause();
    setCurrent(null);
  }, []);

  const seek = useCallback((fraction: number) => {
    const el = ref.current;
    if (el && el.duration) el.currentTime = el.duration * fraction;
  }, []);

  return { current, playing, position, duration, toggle, stop, seek };
}
