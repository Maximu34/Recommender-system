import {
  RecordingPresets,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioPlayer,
  useAudioPlayerStatus,
  useAudioRecorder,
} from 'expo-audio';
import { StatusBar } from 'expo-status-bar';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  audioUrl,
  findSong,
  health,
  matchHum,
  similarByText,
  similarTo,
  type Descriptors,
  type Track,
} from './src/api';
import TrackRow from './src/components/TrackRow';
import Contour from './src/components/Contour';
import NowPlaying from './src/components/NowPlaying';
import MatchCard from './src/components/MatchCard';
import { MAX_HUM_MS } from './src/config';
import { radius, space, theme } from './src/theme';

type Mode = 'song' | 'mood' | 'hum';

/**
 * One-tap entries into mood search. Each is just a text query against CLAP's
 * shared audio-text space, so these are a shortcut into a feature that already
 * works rather than a new set of hardcoded categories.
 */
const MOOD_PRESETS = [
  'acoustic folk guitar',
  'dreamy synth pop',
  'chill lo-fi beats',
  'upbeat indie rock',
  'cinematic ambient',
  'smooth jazz',
];

/** Headline per tab: says what this screen is for in one line. */
const HEADLINES: Record<Mode, { title: string; sub: string }> = {
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
    sub: "Hum, sing or whistle it — a few seconds is enough",
  },
};

/**
 * Mono at 16 kHz: pitch tracking needs no more than that, and it keeps the
 * upload small. The container stays m4a/AAC because Android's MediaRecorder
 * cannot produce WAV -- the backend decodes it with PyAV.
 */
const HUM_RECORDING = {
  ...RecordingPresets.HIGH_QUALITY,
  sampleRate: 16000,
  numberOfChannels: 1,
  bitRate: 64000,
};

export default function App() {
  const [mode, setMode] = useState<Mode>('song');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const [results, setResults] = useState<Track[]>([]);
  const [seed, setSeed] = useState<Track | null>(null);
  const [contour, setContour] = useState<number[] | null>(null);
  const [alternatives, setAlternatives] = useState<Track[]>([]);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [diversity, setDiversity] = useState(0);
  const [engine, setEngine] = useState<'clap' | 'baseline'>('clap');

  const [nowPlaying, setNowPlaying] = useState<Track | null>(null);
  const player = useAudioPlayer();
  const playerStatus = useAudioPlayerStatus(player);
  const recorder = useAudioRecorder(HUM_RECORDING);
  const [recording, setRecording] = useState(false);
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setAudioModeAsync({ playsInSilentMode: true, allowsRecording: false }).catch(
      () => {},
    );
    health()
      .then((h) =>
        setStatus(
          `${h.tracks} tracks · ${h.clap_index} indexed · ${h.melody_index} hummable`,
        ),
      )
      .catch((e: Error) => setError(e.message));
    return () => {
      if (stopTimer.current) clearTimeout(stopTimer.current);
    };
  }, []);

  const run = useCallback(async <T,>(fn: () => Promise<T>, after: (v: T) => void) => {
    setLoading(true);
    setError(null);
    try {
      after(await fn());
    } catch (e) {
      setError((e as Error).message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const doSearch = () => {
    if (!query.trim()) return;
    setSeed(null);
    setContour(null);
    setAlternatives([]);
    setShowAlternatives(false);

    if (mode === 'song') {
      // One request returns the song itself plus what sounds like it, so
      // typing a title or a lyric lands on the song rather than on a list
      // the user then has to tap.
      run(
        () => findSong(query, { engine, diversity }),
        (res) => {
          setSeed(res.match);
          setAlternatives(res.alternatives ?? []);
          setResults(res.results ?? []);
        },
      );
    } else {
      run(
        () => similarByText(query, diversity),
        (res) => setResults(res.results),
      );
    }
  };

  const pickSeed = (track: Track) => {
    setShowAlternatives(false);
    run(
      () => similarTo(track.id, { diversity, engine }),
      (res) => {
        setSeed(res.seed ?? track);
        setResults(res.results);
      },
    );
  };

  // The clip is 30s, so it ends on its own; clear the highlight when it does.
  useEffect(() => {
    if (playerStatus.didJustFinish) setNowPlaying(null);
  }, [playerStatus.didJustFinish]);

  const togglePlay = (track: Track) => {
    if (nowPlaying?.id === track.id) {
      if (playerStatus.playing) player.pause();
      else player.play();
      return;
    }
    player.replace(audioUrl(track));
    player.play();
    setNowPlaying(track);
  };

  const stopPlayback = () => {
    player.pause();
    setNowPlaying(null);
  };

  const startHum = async () => {
    setError(null);
    const perm = await requestRecordingPermissionsAsync();
    if (!perm.granted) {
      setError('Microphone permission is needed to match a hummed tune.');
      return;
    }
    // iOS routes output to the earpiece and drops playback volume while
    // recording is allowed, so only turn it on for the duration of the hum.
    await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
    await recorder.prepareToRecordAsync();
    recorder.record();
    setRecording(true);
    stopTimer.current = setTimeout(stopHum, MAX_HUM_MS);
  };

  const stopHum = async () => {
    if (stopTimer.current) {
      clearTimeout(stopTimer.current);
      stopTimer.current = null;
    }
    if (!recorder.isRecording && !recording) return;
    await recorder.stop();
    await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: false });
    setRecording(false);
    const uri = recorder.uri;
    if (!uri) {
      setError('Recording produced no audio.');
      return;
    }
    setSeed(null);
    setAlternatives([]);
    setShowAlternatives(false);

    run(
      () => matchHum(uri),
      async (res) => {
        setContour(res.contour);
        const [best, ...rest] = res.results;
        if (!best) {
          setResults([]);
          return;
        }
        // The melody match identifies the song; the recommendations below it
        // come from acoustic similarity, same as a typed search. The other
        // melody candidates become the "not this song?" alternatives.
        setSeed(best);
        setAlternatives(rest);
        try {
          const sim = await similarTo(best.id, { diversity, engine });
          setResults(sim.results);
        } catch {
          setResults(rest);
        }
      },
    );
  };

  const seedDescriptors: Descriptors | null | undefined = seed?.descriptors;

  const placeholder = useMemo(
    () =>
      mode === 'song'
        ? 'Search a song by name…'
        : 'Describe a mood — "dreamy guitar, rainy evening"',
    [mode],
  );

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <View style={styles.container}>
        <View style={styles.headerRow}>
          <Text style={styles.brand}>Hummingbird</Text>
          {status ? <Text style={styles.stats}>{status}</Text> : null}
        </View>
        <Text style={styles.heading}>{HEADLINES[mode].title}</Text>
        <Text style={styles.sub}>{HEADLINES[mode].sub}</Text>

        <View style={styles.tabs}>
          {(['song', 'mood', 'hum'] as Mode[]).map((m) => (
            <Pressable
              key={m}
              onPress={() => {
                setMode(m);
                setResults([]);
                setSeed(null);
                setContour(null);
                setError(null);
              }}
              style={[styles.tab, mode === m && styles.tabActive]}
            >
              <Text style={[styles.tabText, mode === m && styles.tabTextActive]}>
                {m === 'song' ? 'By song' : m === 'mood' ? 'By mood' : 'Hum it'}
              </Text>
            </Pressable>
          ))}
        </View>

        {mode !== 'hum' ? (
          <View style={styles.searchRow}>
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder={placeholder}
              placeholderTextColor={theme.textDim}
              style={styles.input}
              returnKeyType="search"
              onSubmitEditing={doSearch}
            />
            <Pressable style={styles.goBtn} onPress={doSearch}>
              <Text style={styles.goText}>Go</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.humBox}>
            <Pressable
              style={[styles.humBtn, recording && styles.humBtnActive]}
              onPress={recording ? stopHum : startHum}
            >
              <Text style={styles.humIcon}>{recording ? '■' : '🎤'}</Text>
            </Pressable>
            <Text style={styles.humHint}>
              {recording
                ? 'Listening… tap to stop'
                : 'Tap and hum the tune for a few seconds'}
            </Text>
            {contour ? <Contour points={contour} /> : null}
          </View>
        )}

        {mode === 'mood' ? (
          <View style={styles.moodWrap}>
            {MOOD_PRESETS.map((m) => (
              <Pressable
                key={m}
                style={styles.moodChip}
                onPress={() => {
                  setQuery(m);
                  setSeed(null);
                  setContour(null);
                  run(
                    () => similarByText(m, diversity),
                    (res) => setResults(res.results),
                  );
                }}
              >
                <Text style={styles.moodChipText}>{m}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}

        {mode === 'song' ? (
          <View style={styles.diversityRow}>
            <Text style={styles.diversityLabel}>Engine</Text>
            {(['baseline', 'clap'] as const).map((e) => (
              <Pressable
                key={e}
                onPress={() => {
                  setEngine(e);
                  if (seed) {
                    run(
                      () => similarTo(seed.id, { diversity, engine: e }),
                      (res) => setResults(res.results),
                    );
                  }
                }}
                style={[styles.pill, engine === e && styles.pillActive]}
              >
                <Text
                  style={[styles.pillText, engine === e && styles.pillTextActive]}
                >
                  {e === 'baseline' ? 'MFCC/chroma' : 'CLAP'}
                </Text>
              </Pressable>
            ))}
          </View>
        ) : null}

        <View style={styles.diversityRow}>
          <Text style={styles.diversityLabel}>Variety</Text>
          {[0, 0.3, 0.6].map((d) => (
            <Pressable
              key={d}
              onPress={() => setDiversity(d)}
              style={[styles.pill, diversity === d && styles.pillActive]}
            >
              <Text
                style={[
                  styles.pillText,
                  diversity === d && styles.pillTextActive,
                ]}
              >
                {d === 0 ? 'Closest' : d === 0.3 ? 'Mixed' : 'Wide'}
              </Text>
            </Pressable>
          ))}
        </View>

        {error ? <Text style={styles.error}>{error}</Text> : null}
        {loading ? (
          <ActivityIndicator color={theme.accent} style={{ marginTop: space(3) }} />
        ) : null}

        <FlatList
          data={results}
          keyExtractor={(t) => String(t.id)}
          contentContainerStyle={{ paddingVertical: space(1.5) }}
          keyboardShouldPersistTaps="handled"
          ListHeaderComponent={
            seed ? (
              <View>
                <MatchCard
                  track={seed}
                  label={mode === 'hum' ? 'we think you hummed' : 'your song'}
                  playing={nowPlaying?.id === seed.id && playerStatus.playing}
                  onPlay={togglePlay}
                  onWrongMatch={
                    alternatives.length
                      ? () => setShowAlternatives((v) => !v)
                      : undefined
                  }
                  wrongMatchLabel={
                    showAlternatives
                      ? 'Hide other matches'
                      : `Not this song? ${alternatives.length} other match${
                          alternatives.length === 1 ? '' : 'es'
                        }`
                  }
                />

                {showAlternatives
                  ? alternatives.map((alt) => (
                      <TrackRow
                        key={alt.id}
                        track={alt}
                        playing={
                          nowPlaying?.id === alt.id && playerStatus.playing
                        }
                        onPlay={togglePlay}
                        onSelect={pickSeed}
                      />
                    ))
                  : null}

                {results.length ? (
                  <Text style={styles.sectionHeading}>
                    Songs that sound like it ·{' '}
                    {engine === 'baseline' ? 'MFCC/chroma' : 'CLAP'}
                  </Text>
                ) : null}
              </View>
            ) : null
          }
          renderItem={({ item }) => (
            <TrackRow
              track={item}
              seed={seedDescriptors}
              playing={nowPlaying?.id === item.id && playerStatus.playing}
              onPlay={togglePlay}
              onSelect={mode === 'song' && !seed ? pickSeed : undefined}
            />
          )}
          ListEmptyComponent={
            !loading && !error ? (
              <Text style={styles.empty}>
                {mode === 'song'
                  ? 'Type a song title, or a line you remember from it.'
                  : mode === 'mood'
                    ? 'Describe the sound you want.'
                    : 'Hum a tune to find it.'}
              </Text>
            ) : null
          }
        />

        {nowPlaying ? (
          <NowPlaying
            track={nowPlaying}
            playing={playerStatus.playing}
            buffering={playerStatus.isBuffering}
            position={playerStatus.currentTime}
            duration={playerStatus.duration}
            onToggle={() => togglePlay(nowPlaying)}
            onClose={stopPlayback}
          />
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.bg },
  container: { flex: 1, paddingHorizontal: space(2), paddingTop: space(1) },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brand: { color: theme.accent, fontSize: 13, fontWeight: '700', letterSpacing: 0.3 },
  stats: { color: theme.textDim, fontSize: 10 },
  heading: {
    color: theme.text,
    fontSize: 23,
    fontWeight: '700',
    letterSpacing: -0.4,
    marginTop: space(1.25),
    lineHeight: 29,
  },
  sub: { color: theme.textDim, fontSize: 12.5, marginTop: 3 },
  moodWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: space(0.75),
    marginTop: space(1.5),
  },
  moodChip: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: radius.lg,
    paddingHorizontal: space(1.5),
    paddingVertical: space(0.875),
  },
  moodChipText: { color: theme.text, fontSize: 12 },
  tabs: {
    flexDirection: 'row',
    backgroundColor: theme.surface,
    borderRadius: radius.lg,
    padding: 4,
    marginTop: space(2),
    borderWidth: 1,
    borderColor: theme.border,
  },
  tab: { flex: 1, paddingVertical: 9, borderRadius: radius.lg, alignItems: 'center' },
  tabActive: { backgroundColor: theme.accent },
  tabText: { color: theme.textDim, fontSize: 13, fontWeight: '600' },
  tabTextActive: { color: '#fff' },
  searchRow: { flexDirection: 'row', gap: space(1), marginTop: space(2) },
  input: {
    flex: 1,
    backgroundColor: theme.surface,
    borderRadius: radius.md,
    paddingHorizontal: space(1.75),
    paddingVertical: space(1.5),
    color: theme.text,
    borderWidth: 1,
    borderColor: theme.border,
    fontSize: 14,
  },
  goBtn: {
    backgroundColor: theme.accent,
    borderRadius: radius.md,
    paddingHorizontal: space(2.25),
    justifyContent: 'center',
  },
  goText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  humBox: { alignItems: 'center', marginTop: space(2.5) },
  humBtn: {
    width: 92,
    height: 92,
    borderRadius: 46,
    backgroundColor: theme.surface,
    borderWidth: 2,
    borderColor: theme.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  humBtnActive: { backgroundColor: theme.danger, borderColor: theme.danger },
  humIcon: { fontSize: 32 },
  humHint: { color: theme.textDim, fontSize: 12.5, marginTop: space(1.25) },
  diversityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space(0.75),
    marginTop: space(2),
  },
  diversityLabel: { color: theme.textDim, fontSize: 12, marginRight: 4 },
  pill: {
    paddingHorizontal: space(1.25),
    paddingVertical: 5,
    borderRadius: radius.lg,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
  },
  pillActive: { backgroundColor: theme.accentSoft, borderColor: theme.accent },
  pillText: { color: theme.textDim, fontSize: 11.5 },
  pillTextActive: { color: theme.text },
  sectionHeading: {
    color: theme.textDim,
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: space(1.25),
  },
  error: {
    color: theme.danger,
    fontSize: 12.5,
    marginTop: space(1.5),
    lineHeight: 18,
  },
  empty: {
    color: theme.textDim,
    fontSize: 13,
    textAlign: 'center',
    marginTop: space(5),
    paddingHorizontal: space(3),
    lineHeight: 19,
  },
});
