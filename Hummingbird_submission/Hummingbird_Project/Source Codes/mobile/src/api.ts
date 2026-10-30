/** Typed client for the recommender backend. */

import { API_BASE, RESULT_COUNT } from './config';

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error(
      `Cannot reach the backend at ${API_BASE}.\n\n` +
        'Check that the laptop and phone share a Wi-Fi network, that uvicorn ' +
        'was started with --host 0.0.0.0, and that API_BASE in src/config.ts ' +
        'matches the address the install gate printed.',
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

export function health() {
  return request<Record<string, unknown>>('/health');
}

/** Title / artist / lyric search — a metadata lookup, not an embedding search. */
export function searchTracks(q: string) {
  return request<Track[]>(`/search?q=${encodeURIComponent(q)}&limit=25`);
}

/**
 * One-step search: the song you meant, plus songs that sound like it.
 *
 * Typing a title or a half-remembered lyric should land on the song itself,
 * not on a list you then have to tap. `alternatives` carries the runners-up
 * for when the top hit is wrong.
 */
export function findSong(
  q: string,
  opts: { engine?: string; diversity?: number } = {},
) {
  const params = new URLSearchParams({
    q,
    k: String(RESULT_COUNT),
    engine: opts.engine ?? 'clap',
    diversity: String(opts.diversity ?? 0),
  });
  return request<FindResponse>(`/find?${params}`);
}

/** "Sounds like this song." */
export function similarTo(
  trackId: number,
  opts: { engine?: string; diversity?: number; sameArtist?: boolean } = {},
) {
  const params = new URLSearchParams({
    k: String(RESULT_COUNT),
    engine: opts.engine ?? 'clap',
    diversity: String(opts.diversity ?? 0),
    same_artist: String(opts.sameArtist ?? true),
  });
  return request<SimilarResponse>(`/similar/${trackId}?${params}`);
}

/** Mood/vibe search — this is the one that uses the CLAP text encoder. */
export function similarByText(text: string, diversity = 0) {
  return request<{ query: string; results: Track[] }>('/similar-by-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, k: RESULT_COUNT, diversity }),
  });
}

/** Upload a hum recording and get melody matches back. */
export async function matchHum(uri: string) {
  const form = new FormData();
  const name = uri.split('/').pop() ?? 'hum.m4a';
  const ext = name.split('.').pop()?.toLowerCase();
  // The backend decodes with PyAV, so whatever the phone records is fine.
  const type = ext === 'wav' ? 'audio/wav' : 'audio/mp4';
  form.append('file', { uri, name, type } as unknown as Blob);

  return request<HumResponse>(`/hum?k=${RESULT_COUNT}`, {
    method: 'POST',
    body: form,
  });
}

/**
 * Where to stream a track's 30-second clip from.
 *
 * Prefer Apple's own public preview URL, which the API already returns. Playing
 * it directly means the backend never serves audio: no object storage to host,
 * no audio bandwidth, and no re-distributing Apple's clips from our own server.
 * That is what lets the backend deploy as a small JSON-only service.
 *
 * Falls back to the backend's own `/audio/{id}` for tracks with no preview URL,
 * which is also the path used during local development.
 *
 * Note: on web this would need Apple's CDN to send CORS headers. The app
 * targets iOS and Android, where that does not apply.
 */
export function audioUrl(track: Track): string {
  return track.preview_url || `${API_BASE}/audio/${track.id}`;
}
