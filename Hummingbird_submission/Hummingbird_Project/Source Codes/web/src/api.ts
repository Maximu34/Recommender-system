/** Typed client for the Hummingbird backend. */

export const API_BASE =
  import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

export const RESULT_COUNT = 20;

export type Descriptors = {
  tempo_bpm: number;
  key: string;
  brightness_hz: number;
  energy: number;
};

export type Track = {
  id: number;
  title: string;
  artist: string;
  album?: string | null;
  genre?: string | null;
  preview_url?: string | null;
  artwork_url?: string | null;
  duration_ms?: number | null;
  source?: string | null;
  similarity?: number;
  score?: number;
  descriptors?: Descriptors | null;
  /** Which field explained the hit: 'title' | 'artist' | 'lyrics'. */
  matched_by?: string;
  /** The single lyric line that matched, when matched_by is 'lyrics'. */
  matched_line?: string | null;
};

export type FindResponse = {
  query: string;
  match: Track | null;
  alternatives: Track[];
  results: Track[];
  engine?: string;
  /** 'title' | 'artist' | 'lyrics' — how the match was found. */
  match_type?: string;
  found_by_title?: boolean;
  /** True when the catalog missed and the song came from a live iTunes lookup. */
  from_itunes?: boolean;
  indexed?: boolean;
  /** True when the backend is analysing the track right now. */
  indexing?: boolean;
  /** True when iTunes could not be reached — distinct from "no such song". */
  itunes_unavailable?: boolean;
  note?: string;
};

export type SimilarResponse = {
  seed: Track | null;
  engine: string;
  results: Track[];
};

export type HumResponse = {
  voiced_ratio: number;
  contour: number[];
  results: Track[];
};

export type Health = {
  status: string;
  db: string;
  tracks: number;
  tracks_with_audio: number;
  clap_index: number;
  baseline_index: number;
  melody_index: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error(
      `Cannot reach the backend at ${API_BASE}. Start it with:\n` +
        'cd backend && uvicorn app.main:app --port 8000',
    );
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    let detail = body;
    try {
      detail = JSON.parse(body).detail ?? body;
    } catch {
      /* not JSON; use the raw body */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export const health = () => request<Health>('/health');

/** Title / artist / lyric search — a metadata lookup, not an embedding search. */
export const searchTracks = (q: string) =>
  request<Track[]>(`/search?q=${encodeURIComponent(q)}&limit=25`);

/**
 * One-step search: the song you meant, plus songs that sound like it.
 *
 * Typing a title or a half-remembered lyric lands on the song itself rather
 * than a list you then have to click.
 */
export const findSong = (
  q: string,
  opts: { engine?: string; diversity?: number } = {},
) =>
  request<FindResponse>(
    `/find?${new URLSearchParams({
      q,
      k: String(RESULT_COUNT),
      engine: opts.engine ?? 'clap',
      diversity: String(opts.diversity ?? 0),
    })}`,
  );

/** "Sounds like this song." */
export const similarTo = (
  trackId: number,
  opts: { engine?: string; diversity?: number } = {},
) =>
  request<SimilarResponse>(
    `/similar/${trackId}?${new URLSearchParams({
      k: String(RESULT_COUNT),
      engine: opts.engine ?? 'clap',
      diversity: String(opts.diversity ?? 0),
    })}`,
  );

/** Mood search — the CLAP text encoder, sharing a space with the audio. */
export const similarByText = (text: string, diversity = 0) =>
  request<{ query: string; results: Track[] }>('/similar-by-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, k: RESULT_COUNT, diversity }),
  });

/**
 * Upload a recorded hum.
 *
 * The browser's MediaRecorder produces webm/opus; the backend decodes with
 * PyAV, which handles Opus, so no conversion is needed here.
 */
export const matchHum = (blob: Blob) => {
  const form = new FormData();
  const ext = blob.type.includes('ogg') ? 'ogg' : 'webm';
  form.append('file', blob, `hum.${ext}`);
  return request<HumResponse>(`/hum?k=${RESULT_COUNT}`, {
    method: 'POST',
    body: form,
  });
};

/**
 * Where to stream a clip from.
 *
 * Apple's own preview URL, which the API already returns. Verified to send
 * `Access-Control-Allow-Origin: *` and to honour range requests, so it plays
 * and seeks cross-origin. Our backend therefore serves no audio at all.
 */
export const audioUrl = (t: Track) =>
  t.preview_url || `${API_BASE}/audio/${t.id}`;
