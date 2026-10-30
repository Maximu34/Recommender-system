import { useCallback, useEffect, useState } from 'react';

import {
  findSong,
  health,
  matchHum,
  similarByText,
  similarTo,
  type Health,
  type Track,
} from './api';
import MatchCard from './components/MatchCard';
import NowPlaying from './components/NowPlaying';
import TrackRow from './components/TrackRow';
import { usePlayer } from './hooks/usePlayer';
import { useRecorder } from './hooks/useRecorder';

type View = 'song' | 'mood' | 'hum';

const HEADLINES: Record<View, { title: string; sub: string }> = {
  song: {
    title: 'Which song are you after?',
    sub: 'Type a title, or a line you remember from it',
  },
  mood: {
    title: 'What should it sound like?',
    sub: 'Describe the feeling, or start from one below',
  },
  hum: {
    title: 'What melody is stuck in your head?',
    sub: 'Hum, sing or whistle it — a few seconds is enough',
  },
};

/**
 * One-tap entries into mood search. Each is plain text sent to the CLAP text
 * encoder, so these are shortcuts into a working feature rather than a fixed
 * set of categories.
 */
const MOODS: { text: string; label: string; color: string }[] = [
  { text: 'acoustic folk guitar', label: 'Acoustic folk', color: '#b45309' },
  { text: 'dreamy synth pop', label: 'Synth pop', color: '#7c3aed' },
  { text: 'chill lo-fi beats', label: 'Chill lo-fi', color: '#0284c7' },
  { text: 'upbeat indie rock', label: 'Upbeat indie', color: '#059669' },
  { text: 'cinematic ambient', label: 'Cinematic', color: '#334155' },
  { text: 'smooth jazz', label: 'Jazz', color: '#c2410c' },
];

export default function App() {
  const [view, setView] = useState<View>('song');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Health | null>(null);

  const [seed, setSeed] = useState<Track | null>(null);
  const [results, setResults] = useState<Track[]>([]);
  const [alternatives, setAlternatives] = useState<Track[]>([]);
  const [showAlts, setShowAlts] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [engine, setEngine] = useState<'clap' | 'baseline'>('clap');
  const [matchLabel, setMatchLabel] = useState('your song');

  const player = usePlayer();
  const recorder = useRecorder();

  useEffect(() => {
    health().then(setStats).catch((e: Error) => setError(e.message));
  }, []);

  const run = useCallback(
    async <T,>(fn: () => Promise<T>, after: (v: T) => void | Promise<void>) => {
      setLoading(true);
      setError(null);
      try {
        await after(await fn());
      } catch (e) {
        setError((e as Error).message);
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const reset = () => {
    setSeed(null);
    setAlternatives([]);
    setShowAlts(false);
    setNote(null);
  };

  const doSearch = () => {
    if (!query.trim()) return;
    reset();
    if (view === 'song') {
      // One request returns the song and its neighbours, so typing a title or
      // a lyric lands on the song rather than on a list to click through.
      void run(
        () => findSong(query, { engine }),
        (res) => {
          setSeed(res.match);
          setAlternatives(res.alternatives ?? []);
          setResults(res.results ?? []);
          setNote(res.note ?? null);
          setMatchLabel(res.from_itunes ? 'found on itunes' : 'your song');

          // The backend is embedding this track in the background. Poll for
          // its recommendations rather than leaving an unexplained empty list
          // -- analysis takes a few seconds, and far longer if the model has
          // to load first.
          if (res.indexing && res.match) void pollForIndex(res.match);
        },
      );
    } else {
      void run(
        () => similarByText(query),
        (res) => setResults(res.results),
      );
    }
  };

  const pollForIndex = async (track: Track) => {
    for (let attempt = 0; attempt < 12; attempt++) {
      await new Promise((r) => setTimeout(r, 4000));
      try {
        const sim = await similarTo(track.id, { engine });
        if (sim.results.length) {
          setResults(sim.results);
          setNote(null);
          setMatchLabel('your song');
          return;
        }
      } catch {
        /* 404 until the embedding exists; keep waiting */
      }
    }
    setNote(
      'Still analysing this song. Search for it again in a moment and the ' +
        'recommendations should be there.',
    );
  };

  const pickSeed = (track: Track) => {
    setShowAlts(false);
    void run(
      () => similarTo(track.id, { engine }),
      (res) => {
        setSeed(res.seed ?? track);
        setResults(res.results);
      },
    );
  };

  const runMood = (text: string) => {
    setQuery(text);
    reset();
    void run(
      () => similarByText(text),
      (res) => setResults(res.results),
    );
  };

  const onHum = async () => {
    if (recorder.recording) {
      recorder.stop();
      return;
    }
    setError(null);
    reset();
    try {
      const blob = await recorder.start();
      if (!blob) {
        setError('Recording produced no audio.');
        return;
      }
      await run(
        () => matchHum(blob),
        async (res) => {
          const [best, ...rest] = res.results;
          if (!best) {
            setResults([]);
            return;
          }
          // The melody match identifies the song; what follows comes from
          // acoustic similarity, the same as a typed search.
          setSeed(best);
          setAlternatives(rest);
          try {
            const sim = await similarTo(best.id, { engine });
            setResults(sim.results);
          } catch {
            setResults(rest);
          }
        },
      );
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const nav = (v: View, icon: string, label: string) => (
    <button
      className={`nav-item${view === v ? ' active' : ''}`}
      onClick={() => {
        setView(v);
        setQuery('');
        setResults([]);
        reset();
        setError(null);
      }}
    >
      <span className="ico">{icon}</span>
      {label}
    </button>
  );

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">♪</span>
          Hummingbird
        </div>
        {nav('song', '⌕', 'Find a song')}
        {nav('mood', '◐', 'By mood')}
        {nav('hum', '🎤', 'Hum to find')}

        <div className="nav-label">Catalog</div>
        <div style={{ padding: '0 11px', fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.8 }}>
          {stats ? (
            <>
              <div>{stats.tracks} tracks</div>
              <div>{stats.clap_index} indexed</div>
              <div>{stats.melody_index} hummable</div>
              <div style={{ color: 'var(--text-faint)', fontSize: 11 }}>
                via {stats.db}
              </div>
            </>
          ) : (
            <div className="muted">connecting…</div>
          )}
        </div>
      </aside>

      <main className="main">
        <div className="head-row">
          <div className="head">
            <h1>{HEADLINES[view].title}</h1>
            <p>{HEADLINES[view].sub}</p>
          </div>
          {view !== 'hum' ? (
            <div className="searchbox">
              <span style={{ color: 'var(--text-faint)' }}>⌕</span>
              <input
                value={query}
                placeholder={
                  view === 'song'
                    ? 'Song title, or a lyric you remember…'
                    : 'dreamy guitar for a rainy evening…'
                }
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && doSearch()}
              />
              {loading ? <span className="spin" /> : null}
            </div>
          ) : null}
        </div>

        {view === 'song' ? (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 16 }}>
            <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>Engine</span>
            {(['clap', 'baseline'] as const).map((e) => (
              <button
                key={e}
                className="chip"
                style={
                  engine === e
                    ? { background: 'var(--accent-soft)', color: 'var(--accent-deep)' }
                    : undefined
                }
                onClick={() => {
                  setEngine(e);
                  if (seed) pickSeed(seed);
                }}
              >
                {e === 'clap' ? 'CLAP' : 'MFCC/chroma'}
              </button>
            ))}
          </div>
        ) : null}

        {view === 'hum' ? (
          <div className="panel hum-panel" style={{ marginTop: 18 }}>
            <div className="pill">
              <span className="dot" />
              {recorder.recording ? 'Listening…' : 'Ready when you are'}
            </div>
            <div className="bars">
              {(recorder.level.length
                ? recorder.level
                : Array.from({ length: 48 }, () => 0)
              ).map((v, i) => (
                <div
                  key={i}
                  className="bar"
                  style={{
                    height: Math.max(3, v * 62),
                    opacity: recorder.recording ? 1 : 0.28,
                  }}
                />
              ))}
            </div>
            <button
              className={`rec-btn${recorder.recording ? ' recording' : ''}`}
              onClick={onHum}
              disabled={loading}
            >
              {recorder.recording
                ? `■  Stop  ${recorder.elapsed.toFixed(1)}s`
                : '🎤  Start humming'}
            </button>
            <span className="muted" style={{ fontSize: 12 }}>
              Records up to 10 seconds. Needs microphone permission.
            </span>
          </div>
        ) : null}

        {view === 'mood' ? (
          <div className="tiles" style={{ marginTop: 18 }}>
            {MOODS.map((m) => (
              <button
                key={m.text}
                className="tile"
                style={{ background: m.color }}
                onClick={() => runMood(m.text)}
              >
                {m.label}
              </button>
            ))}
          </div>
        ) : null}

        {error ? (
          <div className="error" style={{ marginTop: 18 }}>
            {error}
          </div>
        ) : null}

        {!seed && note ? (
          <p className="muted" style={{ marginTop: 18, lineHeight: 1.6 }}>
            {note}
          </p>
        ) : null}

        {seed ? (
          <div style={{ marginTop: 18 }}>
            <MatchCard
              track={seed}
              label={view === 'hum' ? 'we think you hummed' : matchLabel}
              playing={player.current?.id === seed.id && player.playing}
              onPlay={player.toggle}
              onToggleAlternatives={
                alternatives.length ? () => setShowAlts((v) => !v) : undefined
              }
              alternativesLabel={
                showAlts
                  ? 'Hide other matches'
                  : `Not this song? ${alternatives.length} other match${
                      alternatives.length === 1 ? '' : 'es'
                    }`
              }
            />
            {note ? (
              <p
                className="muted"
                style={{ marginTop: 10, fontSize: 12.5, lineHeight: 1.55 }}
              >
                {note}
              </p>
            ) : null}
            {showAlts ? (
              <div className="panel" style={{ marginTop: 11 }}>
                {alternatives.map((a) => (
                  <TrackRow
                    key={a.id}
                    track={a}
                    playing={player.current?.id === a.id && player.playing}
                    onPlay={player.toggle}
                    onSelect={pickSeed}
                  />
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {results.length ? (
          <div className="panel" style={{ marginTop: 18 }}>
            <h3 className="section-title">
              {seed ? 'Songs that sound like it' : 'Results'}
              <span className="chip">
                {engine === 'clap' ? 'CLAP' : 'MFCC/chroma'}
              </span>
            </h3>
            {results.map((t) => (
              <TrackRow
                key={t.id}
                track={t}
                seed={seed?.descriptors}
                playing={player.current?.id === t.id && player.playing}
                onPlay={player.toggle}
              />
            ))}
          </div>
        ) : null}

        {!results.length && !seed && !loading && !error ? (
          <p className="muted" style={{ marginTop: 28 }}>
            {view === 'song'
              ? 'Try “bohemian”, or a lyric like “caught in a landslide”.'
              : view === 'mood'
                ? 'Pick a tile above, or describe a sound in your own words.'
                : 'Hum a tune and Hummingbird will try to name it.'}
          </p>
        ) : null}
      </main>

      <NowPlaying
        track={player.current}
        playing={player.playing}
        position={player.position}
        duration={player.duration}
        onToggle={() => player.current && player.toggle(player.current)}
        onSeek={player.seek}
      />
    </div>
  );
}
