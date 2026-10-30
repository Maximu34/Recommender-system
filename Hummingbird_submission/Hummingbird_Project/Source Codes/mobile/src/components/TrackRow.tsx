import React, { useState } from 'react';
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import type { Descriptors, Track } from '../api';
import { radius, space, theme } from '../theme';

type Props = {
  track: Track;
  seed?: Descriptors | null;
  playing: boolean;
  onPlay: (track: Track) => void;
  onSelect?: (track: Track) => void;
};

/** Plain-language reasons this track resembles the seed. */
function explain(a?: Descriptors | null, b?: Descriptors | null): string[] {
  if (!a || !b) return [];
  const out: string[] = [];

  const dTempo = Math.abs(a.tempo_bpm - b.tempo_bpm);
  if (dTempo < 6) out.push(`same tempo (~${Math.round(b.tempo_bpm)} BPM)`);
  else if (dTempo < 15) out.push(`similar tempo (${Math.round(b.tempo_bpm)} BPM)`);

  if (a.key === b.key) out.push(`same key (${b.key})`);
  else if (a.key.split(' ')[1] === b.key.split(' ')[1])
    out.push(`both ${b.key.split(' ')[1]}`);

  const ratio = b.brightness_hz / (a.brightness_hz || 1);
  if (ratio > 0.85 && ratio < 1.18) out.push('similar brightness');
  else if (ratio >= 1.18) out.push('brighter');
  else out.push('darker');

  const eRatio = b.energy / (a.energy || 1e-6);
  if (eRatio > 0.8 && eRatio < 1.25) out.push('similar energy');

  return out.slice(0, 3);
}

export default function TrackRow({ track, seed, playing, onPlay, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const score = track.similarity ?? track.score;
  const reasons = explain(seed, track.descriptors);

  return (
    <View style={styles.wrap}>
      <Pressable
        style={styles.row}
        onPress={() => (onSelect ? onSelect(track) : setOpen((v) => !v))}
      >
        {track.artwork_url ? (
          <Image source={{ uri: track.artwork_url }} style={styles.art} />
        ) : (
          <View style={[styles.art, styles.artFallback]} />
        )}

        <View style={styles.meta}>
          <Text style={styles.title} numberOfLines={1}>
            {track.title}
          </Text>
          <Text style={styles.artist} numberOfLines={1}>
            {track.artist}
          </Text>

          <View style={styles.chips}>
            {track.genre ? (
              <View style={styles.chip}>
                <Text style={styles.chipText}>{track.genre}</Text>
              </View>
            ) : null}
            {score !== undefined ? (
              <View style={styles.scoreWrap}>
                <View style={styles.scoreTrack}>
                  <View
                    style={[
                      styles.scoreFill,
                      { width: `${Math.max(4, Math.min(100, score * 100))}%` },
                    ]}
                  />
                </View>
                <Text style={styles.scoreText}>{score.toFixed(2)}</Text>
              </View>
            ) : null}
          </View>
        </View>

        <Pressable
          hitSlop={10}
          style={[styles.play, playing && styles.playActive]}
          onPress={() => onPlay(track)}
        >
          <Text style={styles.playIcon}>{playing ? '■' : '▶'}</Text>
        </Pressable>
      </Pressable>

      {reasons.length > 0 ? (
        <Pressable onPress={() => setOpen((v) => !v)} style={styles.whyBar}>
          <Text style={styles.whyText}>
            {open ? '▾ ' : '▸ '}
            {open ? 'why this one' : reasons.join(' · ')}
          </Text>
        </Pressable>
      ) : null}

      {open && track.descriptors ? (
        <View style={styles.detail}>
          {reasons.map((r) => (
            <Text key={r} style={styles.reason}>
              • {r}
            </Text>
          ))}
          <Text style={styles.raw}>
            {Math.round(track.descriptors.tempo_bpm)} BPM · {track.descriptors.key} ·{' '}
            {Math.round(track.descriptors.brightness_hz)} Hz centroid
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: theme.surface,
    borderRadius: radius.md,
    marginBottom: space(1.25),
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: theme.border,
  },
  row: { flexDirection: 'row', alignItems: 'center', padding: space(1.25) },
  art: { width: 54, height: 54, borderRadius: radius.sm, marginRight: space(1.5) },
  artFallback: { backgroundColor: theme.accentSoft },
  meta: { flex: 1, minWidth: 0 },
  title: { color: theme.text, fontSize: 15, fontWeight: '600' },
  artist: { color: theme.textDim, fontSize: 13, marginTop: 2 },
  chips: { flexDirection: 'row', alignItems: 'center', marginTop: 6, gap: 8 },
  chip: {
    backgroundColor: theme.surfaceAlt,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  chipText: { color: theme.textDim, fontSize: 11 },
  scoreWrap: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: 6 },
  scoreTrack: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    backgroundColor: theme.surfaceAlt,
    overflow: 'hidden',
  },
  scoreFill: { height: 4, backgroundColor: theme.accent },
  scoreText: { color: theme.textDim, fontSize: 11, width: 32 },
  play: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.surfaceAlt,
    marginLeft: space(1),
  },
  playActive: { backgroundColor: theme.accent },
  playIcon: { color: theme.text, fontSize: 14 },
  whyBar: {
    paddingHorizontal: space(1.5),
    paddingBottom: space(1),
    paddingTop: 0,
  },
  whyText: { color: theme.textDim, fontSize: 11.5 },
  detail: {
    paddingHorizontal: space(1.5),
    paddingBottom: space(1.5),
    gap: 3,
  },
  reason: { color: theme.text, fontSize: 12.5 },
  raw: { color: theme.textDim, fontSize: 11, marginTop: 4 },
});
