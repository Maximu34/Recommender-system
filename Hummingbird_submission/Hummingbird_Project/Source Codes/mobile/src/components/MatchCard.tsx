import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import type { Track } from '../api';
import { radius, space, theme } from '../theme';

type Props = {
  track: Track;
  label: string;
  playing: boolean;
  onPlay: (track: Track) => void;
  onWrongMatch?: () => void;
  wrongMatchLabel?: string;
};

/**
 * The song the user was actually looking for, shown above the recommendations.
 *
 * Deliberately larger and visually distinct from a result row: it answers
 * "did we find your song?" before the list answers "what else sounds like it?".
 * When the hit came from a lyric, the matching line is shown so the match
 * explains itself rather than looking arbitrary.
 */
export default function MatchCard({
  track,
  label,
  playing,
  onPlay,
  onWrongMatch,
  wrongMatchLabel,
}: Props) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>

      <View style={styles.row}>
        {track.artwork_url ? (
          <Image source={{ uri: track.artwork_url }} style={styles.art} />
        ) : (
          <View style={[styles.art, styles.artFallback]} />
        )}

        <View style={styles.meta}>
          <Text style={styles.title} numberOfLines={2}>
            {track.title}
          </Text>
          <Text style={styles.artist} numberOfLines={1}>
            {track.artist}
          </Text>
          {track.genre ? (
            <View style={styles.chip}>
              <Text style={styles.chipText}>{track.genre}</Text>
            </View>
          ) : null}
        </View>

        <Pressable
          hitSlop={10}
          style={[styles.play, playing && styles.playActive]}
          onPress={() => onPlay(track)}
        >
          <Text style={styles.playIcon}>{playing ? '❚❚' : '▶'}</Text>
        </Pressable>
      </View>

      {track.matched_line ? (
        <View style={styles.lyricBox}>
          <Text style={styles.lyricLabel}>matched this line</Text>
          <Text style={styles.lyric} numberOfLines={2}>
            “{track.matched_line}”
          </Text>
        </View>
      ) : null}

      {onWrongMatch ? (
        <Pressable onPress={onWrongMatch} style={styles.wrong}>
          <Text style={styles.wrongText}>
            {wrongMatchLabel ?? 'Not this song?'}
          </Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: theme.surfaceAlt,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: theme.accent,
    padding: space(1.5),
    marginBottom: space(2),
  },
  label: {
    color: theme.accent,
    fontSize: 10.5,
    fontWeight: '600',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    marginBottom: space(1),
  },
  row: { flexDirection: 'row', alignItems: 'center' },
  art: { width: 68, height: 68, borderRadius: radius.sm, marginRight: space(1.5) },
  artFallback: { backgroundColor: theme.accentSoft },
  meta: { flex: 1, minWidth: 0 },
  title: { color: theme.text, fontSize: 17, fontWeight: '700' },
  artist: { color: theme.textDim, fontSize: 13.5, marginTop: 2 },
  chip: {
    alignSelf: 'flex-start',
    backgroundColor: theme.surface,
    borderRadius: radius.sm,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginTop: 6,
  },
  chipText: { color: theme.textDim, fontSize: 10.5 },
  play: {
    width: 46,
    height: 46,
    borderRadius: 23,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.accent,
    marginLeft: space(1),
  },
  playActive: { backgroundColor: theme.good },
  playIcon: { color: '#fff', fontSize: 15 },
  lyricBox: {
    marginTop: space(1.25),
    backgroundColor: theme.surface,
    borderRadius: radius.sm,
    padding: space(1),
  },
  lyricLabel: { color: theme.textDim, fontSize: 9.5, marginBottom: 3 },
  lyric: { color: theme.text, fontSize: 12.5, fontStyle: 'italic', lineHeight: 18 },
  wrong: { marginTop: space(1.25) },
  wrongText: { color: theme.textDim, fontSize: 11.5, textDecorationLine: 'underline' },
});
